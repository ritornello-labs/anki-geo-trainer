/*
 * GeoTrainer interaction engine — F3 Locate (M0 spike).
 *
 * Runs inside an Anki card on Desktop (QtWebEngine), AnkiMobile (WebKit), and
 * AnkiDroid (Android WebView). Cross-platform rules baked in:
 *   - No dependence on script load order: boot() polls for the DOM + data and
 *     self-triggers, so it works whether this <script> ran before or after the
 *     card HTML was injected (AnkiMobile loads async / out of order).
 *   - No media dependence: the engine and the scope bundle are inlined into the
 *     card templates; nothing is fetched from collection.media.
 *   - Front->back attempt handoff via localStorage (persists across the reveal
 *     on all three platforms; sessionStorage does not, per workspace lessons).
 *   - Self-grading only: the back shows a verdict + suggested grade; the user
 *     still presses the Anki grade button. No platform answer-API dependency.
 *
 * A card container looks like:
 *   <div class="gt-app" data-side="front|back"
 *        data-scope="us-states" data-target="US-CA"></div>
 * with the scope bundle available as window.GT_BUNDLES["us-states"].
 */
(function () {
  "use strict";

  var NS = "geotrainer";

  // ---- geometry helpers -----------------------------------------------------

  function pointInRing(x, y, ring) {
    // Ray casting; ring is [[x,y],...].
    var inside = false;
    for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      var xi = ring[i][0], yi = ring[i][1];
      var xj = ring[j][0], yj = ring[j][1];
      var intersect =
        yi > y !== yj > y &&
        x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
      if (intersect) inside = !inside;
    }
    return inside;
  }

  function pointInRegion(x, y, region) {
    // Disjoint exterior rings (holes dropped in the pipeline): inside iff inside
    // any single ring.
    for (var i = 0; i < region.rings.length; i++) {
      if (pointInRing(x, y, region.rings[i])) return true;
    }
    return false;
  }

  function regionAt(x, y, bundle) {
    for (var i = 0; i < bundle.regions.length; i++) {
      if (pointInRegion(x, y, bundle.regions[i])) return bundle.regions[i];
    }
    return null;
  }

  function findRegion(bundle, id) {
    for (var i = 0; i < bundle.regions.length; i++) {
      if (bundle.regions[i].id === id) return bundle.regions[i];
    }
    return null;
  }

  // ---- rendering ------------------------------------------------------------

  var SVGNS = "http://www.w3.org/2000/svg";

  function el(name, attrs) {
    var node = document.createElementNS(SVGNS, name);
    if (attrs) {
      for (var k in attrs) if (attrs.hasOwnProperty(k)) node.setAttribute(k, attrs[k]);
    }
    return node;
  }

  function ringPath(rings) {
    var d = "";
    for (var i = 0; i < rings.length; i++) {
      var r = rings[i];
      d += "M" + r[0][0] + "," + r[0][1];
      for (var k = 1; k < r.length; k++) d += "L" + r[k][0] + "," + r[k][1];
      d += "Z";
    }
    return d;
  }

  function buildSvg(bundle) {
    var v = bundle.view;
    var svg = el("svg", {
      viewBox: "0 0 " + v.w + " " + v.h,
      class: "gt-map",
      role: "img",
    });
    var bg = el("rect", { x: 0, y: 0, width: v.w, height: v.h, class: "gt-ocean" });
    svg.appendChild(bg);
    var land = el("g", { class: "gt-land" });
    var byId = {};
    for (var i = 0; i < bundle.regions.length; i++) {
      var reg = bundle.regions[i];
      var p = el("path", { d: ringPath(reg.rings), class: "gt-region", "data-id": reg.id });
      land.appendChild(p);
      byId[reg.id] = p;
    }
    svg.appendChild(land);
    return { svg: svg, byId: byId };
  }

  function svgPoint(svg, clientX, clientY) {
    var pt = svg.createSVGPoint();
    pt.x = clientX;
    pt.y = clientY;
    var ctm = svg.getScreenCTM();
    if (!ctm) return null;
    var loc = pt.matrixTransform(ctm.inverse());
    return { x: loc.x, y: loc.y };
  }

  // ---- attempt storage ------------------------------------------------------

  function attemptKey(scope, target) {
    return NS + ":attempt:" + scope + ":" + target;
  }

  function saveAttempt(scope, target, attempt) {
    try {
      localStorage.setItem(attemptKey(scope, target), JSON.stringify(attempt));
    } catch (e) {
      // Private mode / disabled storage: fall back to a window global so the
      // back side can still read it if the platform kept the JS context.
      window["__gt_attempt_" + scope + "_" + target] = attempt;
    }
  }

  function loadAttempt(scope, target) {
    try {
      var raw = localStorage.getItem(attemptKey(scope, target));
      if (raw) return JSON.parse(raw);
    } catch (e) {
      /* fall through */
    }
    return window["__gt_attempt_" + scope + "_" + target] || null;
  }

  // ---- UI chrome ------------------------------------------------------------

  function chip(text) {
    var c = document.createElement("div");
    c.className = "gt-chip";
    c.textContent = text;
    return c;
  }

  function bar(text, cls) {
    var b = document.createElement("div");
    b.className = "gt-bar " + (cls || "");
    b.textContent = text;
    return b;
  }

  // ---- front ----------------------------------------------------------------

  function mountFront(root, bundle, target) {
    var region = findRegion(bundle, target);
    var name = region ? region.name : target;

    root.innerHTML = "";
    root.appendChild(chip("Locate"));
    var prompt = document.createElement("div");
    prompt.className = "gt-prompt";
    prompt.textContent = name;
    root.appendChild(prompt);

    var built = buildSvg(bundle);
    var svg = built.svg;
    var marker = el("circle", { r: 9, class: "gt-attempt", style: "display:none" });
    svg.appendChild(marker);
    root.appendChild(svg);

    var hint = bar("Tap the map where it is", "gt-hint");
    root.appendChild(hint);

    var placed = false;

    function place(clientX, clientY) {
      var loc = svgPoint(svg, clientX, clientY);
      if (!loc) return;
      marker.setAttribute("cx", loc.x);
      marker.setAttribute("cy", loc.y);
      marker.style.display = "";
      placed = true;
      var hit = regionAt(loc.x, loc.y, bundle);
      saveAttempt(bundle.scope, target, {
        x: loc.x,
        y: loc.y,
        hitId: hit ? hit.id : null,
      });
      hint.textContent = "Tap again to adjust · flip to check";
      hint.className = "gt-bar gt-hint gt-placed";
    }

    svg.addEventListener("click", function (ev) {
      place(ev.clientX, ev.clientY);
    });
    // Touch: use touchend so a tap doesn't scroll-cancel; clientX from the touch.
    svg.addEventListener(
      "touchend",
      function (ev) {
        if (ev.changedTouches && ev.changedTouches.length) {
          var t = ev.changedTouches[0];
          place(t.clientX, t.clientY);
          ev.preventDefault();
        }
      },
      { passive: false }
    );

    // Clear any stale attempt from a previous review of this same card.
    saveAttempt(bundle.scope, target, null);
    void placed;
  }

  // ---- back -----------------------------------------------------------------

  function distanceKm(ax, ay, region, bundle) {
    var dx = ax - region.c[0];
    var dy = ay - region.c[1];
    return Math.sqrt(dx * dx + dy * dy) * bundle.view.kmPerUnit;
  }

  function mountBack(root, bundle, target) {
    var region = findRegion(bundle, target);
    var name = region ? region.name : target;
    var attempt = loadAttempt(bundle.scope, target);

    root.innerHTML = "";
    root.appendChild(chip("Locate"));
    var prompt = document.createElement("div");
    prompt.className = "gt-prompt";
    prompt.textContent = name;
    root.appendChild(prompt);

    var built = buildSvg(bundle);
    var svg = built.svg;

    // Highlight the answer region.
    if (built.byId[target]) built.byId[target].classList.add("gt-answer");

    // Draw the user's attempt + a link to the target centroid.
    var correct = false;
    if (attempt) {
      correct = region ? pointInRegion(attempt.x, attempt.y, region) : false;
      if (region && !correct) {
        var line = el("line", {
          x1: attempt.x,
          y1: attempt.y,
          x2: region.c[0],
          y2: region.c[1],
          class: "gt-link",
        });
        svg.appendChild(line);
      }
      var m = el("circle", {
        cx: attempt.x,
        cy: attempt.y,
        r: 9,
        class: "gt-attempt " + (correct ? "gt-good" : "gt-bad"),
      });
      svg.appendChild(m);
    }
    root.appendChild(svg);

    var verdict, cls, suggestion;
    if (!attempt) {
      verdict = "No tap recorded — answer: " + name;
      cls = "gt-miss";
      suggestion = "Grade: Again";
    } else if (correct) {
      verdict = "Correct — inside " + name;
      cls = "gt-ok";
      suggestion = "Grade: Good / Easy";
    } else {
      var km = Math.round(distanceKm(attempt.x, attempt.y, region, bundle));
      var hitName = attempt.hitId ? (findRegion(bundle, attempt.hitId) || {}).name : null;
      verdict =
        "Missed by ~" + km + " km" + (hitName ? " (you tapped " + hitName + ")" : "");
      cls = "gt-miss";
      suggestion = km < 250 ? "Grade: Hard" : "Grade: Again";
    }
    root.appendChild(bar(verdict, cls));
    root.appendChild(bar(suggestion, "gt-suggest"));
  }

  // ---- boot -----------------------------------------------------------------

  function mount(root) {
    if (!root || root.getAttribute("data-gt-mounted") === "1") return;
    var scope = root.getAttribute("data-scope");
    var target = root.getAttribute("data-target");
    var side = root.getAttribute("data-side") || "front";
    var bundle = window.GT_BUNDLES && window.GT_BUNDLES[scope];
    if (!bundle) return; // bundle script not evaluated yet; boot() will retry
    root.setAttribute("data-gt-mounted", "1");
    if (side === "back") mountBack(root, bundle, target);
    else mountFront(root, bundle, target);
  }

  function mountAll() {
    var nodes = document.querySelectorAll(".gt-app:not([data-gt-mounted='1'])");
    for (var i = 0; i < nodes.length; i++) mount(nodes[i]);
  }

  var tries = 0;
  function boot() {
    mountAll();
    // Retry for a short window to cover async/out-of-order script + DOM readiness.
    var pending = document.querySelectorAll(".gt-app:not([data-gt-mounted='1'])");
    if (pending.length && tries++ < 60) {
      setTimeout(boot, 50);
    }
  }

  window.GeoTrainer = { mount: mount, mountAll: mountAll, _boot: boot };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  }
  boot();
})();
