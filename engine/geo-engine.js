/*
 * GeoTrainer interaction engine — F3 Locate, F4 Point-in-region, F5 Place-the-piece.
 *
 * Runs inside an Anki card on Desktop (QtWebEngine), AnkiMobile (WebKit), and
 * AnkiDroid (Android WebView). Cross-platform rules baked in:
 *   - No dependence on script load order: boot() polls for the DOM + data and
 *     self-triggers, so it works whether this <script> ran before or after the
 *     card HTML was injected (AnkiMobile loads async / out of order).
 *   - No media dependence: the engine and the scope bundle are inlined into the
 *     card templates; nothing is fetched from collection.media.
 *   - Front->back state handoff via localStorage (persists across the reveal on
 *     all three platforms; sessionStorage does not, per workspace lessons), with
 *     a deterministic day-seeded fallback for F4 so front and back agree even if
 *     storage is unavailable.
 *   - Self-grading only: the back shows a verdict + suggested grade; the user
 *     still presses the Anki grade button. No platform answer-API dependency.
 *
 * A card container looks like:
 *   <div class="gt-app" data-side="front|back" data-mode="locate|point|place"
 *        data-scope="us-states" data-target="US-CA"></div>
 * with the scope bundle available as window.GT_BUNDLES["us-states"].
 *
 * Bundle geometry is PRE-PROJECTED: every coordinate is already in one shared
 * pixel space. Inset panels (e.g. Alaska/Hawaii) are separate projection
 * "frames" with their own kmPerUnit; distances are only reported when both
 * points share a frame.
 */
(function () {
  "use strict";

  var NS = "geotrainer";

  // ---- deterministic PRNG (portable; mirrored in scripts/build_bundle.py) ----

  function strHash(s) {
    var h = 2166136261;
    for (var i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 16777619) >>> 0;
    }
    return h >>> 0;
  }

  function dayStamp() {
    var d = new Date();
    var m = d.getMonth() + 1, day = d.getDate();
    return d.getFullYear() + "-" + (m < 10 ? "0" + m : m) + "-" + (day < 10 ? "0" + day : day);
  }

  // ---- geometry helpers -------------------------------------------------------

  function pointInRing(x, y, ring) {
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

  function frameOf(bundle, x, y) {
    // Non-main frames are drawn boxes; check them first, else main.
    var main = null;
    for (var i = 0; i < bundle.frames.length; i++) {
      var f = bundle.frames[i];
      if (f.id === "main") { main = f; continue; }
      var r = f.rect;
      if (x >= r[0] && x <= r[0] + r[2] && y >= r[1] && y <= r[1] + r[3]) return f;
    }
    return main;
  }

  function frameById(bundle, id) {
    for (var i = 0; i < bundle.frames.length; i++) {
      if (bundle.frames[i].id === id) return bundle.frames[i];
    }
    return null;
  }

  // ---- rendering --------------------------------------------------------------

  var SVGNS = "http://www.w3.org/2000/svg";

  function el(name, attrs) {
    var node = document.createElementNS(SVGNS, name);
    if (attrs) {
      for (var k in attrs) if (attrs.hasOwnProperty(k)) node.setAttribute(k, attrs[k]);
    }
    return node;
  }

  function ringPath(rings, dx, dy) {
    dx = dx || 0; dy = dy || 0;
    var d = "";
    for (var i = 0; i < rings.length; i++) {
      var r = rings[i];
      d += "M" + (r[0][0] + dx) + "," + (r[0][1] + dy);
      for (var k = 1; k < r.length; k++) d += "L" + (r[k][0] + dx) + "," + (r[k][1] + dy);
      d += "Z";
    }
    return d;
  }

  function buildSvg(bundle) {
    var v = bundle.view;
    var svg = el("svg", { viewBox: "0 0 " + v.w + " " + v.h, class: "gt-map", role: "img" });
    svg.appendChild(el("rect", { x: 0, y: 0, width: v.w, height: v.h, class: "gt-ocean" }));

    // Inset frame boxes behind the land.
    for (var i = 0; i < bundle.frames.length; i++) {
      var f = bundle.frames[i];
      if (f.id === "main") continue;
      svg.appendChild(
        el("rect", {
          x: f.rect[0], y: f.rect[1], width: f.rect[2], height: f.rect[3],
          rx: 6, class: "gt-frame",
        })
      );
    }

    // Neutral context land (non-quiz landmass) for orientation, under the regions.
    if (bundle.context && bundle.context.length) {
      svg.appendChild(el("path", { d: ringPath(bundle.context), class: "gt-context" }));
    }

    var land = el("g", { class: "gt-land" });
    var byId = {};
    for (var k = 0; k < bundle.regions.length; k++) {
      var reg = bundle.regions[k];
      var cls = "gt-region" + (reg.small ? " gt-small" : "") + (reg.tier === 2 ? " gt-tier2" : "");
      var p = el("path", { d: ringPath(reg.rings), class: cls, "data-id": reg.id });
      land.appendChild(p);
      byId[reg.id] = p;
    }
    svg.appendChild(land);
    return { svg: svg, byId: byId };
  }

  function nounOf(bundle) {
    return bundle.noun || "region";
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

  // ---- state storage ----------------------------------------------------------

  function storeKey(mode, scope, target) {
    return NS + ":" + mode + ":" + scope + ":" + target;
  }

  function saveState(mode, scope, target, state) {
    try {
      localStorage.setItem(storeKey(mode, scope, target), JSON.stringify(state));
    } catch (e) {
      window["__gt_" + mode + "_" + scope + "_" + target] = state;
    }
  }

  function loadState(mode, scope, target) {
    try {
      var raw = localStorage.getItem(storeKey(mode, scope, target));
      if (raw) return JSON.parse(raw);
    } catch (e) { /* fall through */ }
    return window["__gt_" + mode + "_" + scope + "_" + target] || null;
  }

  // ---- UI chrome ----------------------------------------------------------------

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

  function prompt(text) {
    var p = document.createElement("div");
    p.className = "gt-prompt";
    p.textContent = text;
    return p;
  }

  function suggestFor(quality) {
    // quality: 2 good, 1 close, 0 miss
    return quality === 2 ? "Grade: Good / Easy" : quality === 1 ? "Grade: Hard" : "Grade: Again";
  }

  function kmBetween(bundle, ax, ay, bx, by, frameA, frameB) {
    if (!frameA || !frameB || frameA.id !== frameB.id) return null;
    var dx = ax - bx, dy = ay - by;
    return Math.round(Math.sqrt(dx * dx + dy * dy) * frameA.kmPerUnit);
  }

  // ============================ F3: LOCATE =====================================

  function locateFront(root, bundle, target) {
    var region = findRegion(bundle, target);
    root.appendChild(chip("Locate"));
    root.appendChild(prompt(region ? region.name : target));

    var built = buildSvg(bundle);
    var svg = built.svg;
    var marker = el("circle", { r: 9, class: "gt-attempt", style: "display:none" });
    svg.appendChild(marker);
    root.appendChild(svg);

    var hint = bar("Tap the map where it is", "gt-hint");
    root.appendChild(hint);

    function place(clientX, clientY) {
      var loc = svgPoint(svg, clientX, clientY);
      if (!loc) return;
      marker.setAttribute("cx", loc.x);
      marker.setAttribute("cy", loc.y);
      marker.style.display = "";
      var hit = regionAt(loc.x, loc.y, bundle);
      saveState("locate", bundle.scope, target, {
        x: loc.x, y: loc.y, hitId: hit ? hit.id : null,
      });
      hint.textContent = "Tap again to adjust · flip to check";
      hint.className = "gt-bar gt-hint gt-placed";
    }

    svg.addEventListener("click", function (ev) { place(ev.clientX, ev.clientY); });
    svg.addEventListener("touchend", function (ev) {
      if (ev.changedTouches && ev.changedTouches.length) {
        var t = ev.changedTouches[0];
        place(t.clientX, t.clientY);
        ev.preventDefault();
      }
    }, { passive: false });

    saveState("locate", bundle.scope, target, null); // clear stale attempt
  }

  function locateBack(root, bundle, target) {
    var region = findRegion(bundle, target);
    var attempt = loadState("locate", bundle.scope, target);

    root.appendChild(chip("Locate"));
    root.appendChild(prompt(region ? region.name : target));

    var built = buildSvg(bundle);
    var svg = built.svg;
    if (built.byId[target]) built.byId[target].classList.add("gt-answer");

    var correct = false;
    if (attempt && region) {
      correct = pointInRegion(attempt.x, attempt.y, region);
      if (!correct) {
        svg.appendChild(el("line", {
          x1: attempt.x, y1: attempt.y, x2: region.c[0], y2: region.c[1], class: "gt-link",
        }));
      }
      svg.appendChild(el("circle", {
        cx: attempt.x, cy: attempt.y, r: 9,
        class: "gt-attempt " + (correct ? "gt-good" : "gt-bad"),
      }));
    }
    root.appendChild(svg);

    if (!attempt) {
      root.appendChild(bar("No tap recorded — answer: " + region.name, "gt-miss"));
      root.appendChild(bar(suggestFor(0), "gt-suggest"));
      return;
    }
    if (correct) {
      root.appendChild(bar("Correct — inside " + region.name, "gt-ok"));
      root.appendChild(bar(suggestFor(2), "gt-suggest"));
      return;
    }
    var attemptFrame = frameOf(bundle, attempt.x, attempt.y);
    var targetFrame = frameById(bundle, region.frame);
    var km = kmBetween(bundle, attempt.x, attempt.y, region.c[0], region.c[1], attemptFrame, targetFrame);
    var hitName = attempt.hitId ? (findRegion(bundle, attempt.hitId) || {}).name : null;
    var msg;
    if (km !== null) {
      msg = "Missed by ~" + km + " km" + (hitName ? " (you tapped " + hitName + ")" : "");
    } else {
      msg = (hitName ? "You tapped " + hitName + " — " : "") + region.name +
        " is in the inset panel";
    }
    root.appendChild(bar(msg, "gt-miss"));
    root.appendChild(bar(suggestFor(km !== null && km < 250 ? 1 : 0), "gt-suggest"));
  }

  // ========================= F4: POINT-IN-REGION ===============================

  function pointIndex(bundle, target) {
    // Deterministic per (card, day): front and back agree even without storage;
    // varies across review days. Storage smooths a midnight flip.
    var stored = loadState("point", bundle.scope, target);
    var today = dayStamp();
    if (stored && stored.day === today && typeof stored.idx === "number") return stored.idx;
    var region = findRegion(bundle, target);
    var idx = strHash(target + ":" + today) % region.pts.length;
    saveState("point", bundle.scope, target, { idx: idx, day: today });
    return idx;
  }

  function pointDot(svg, region, idx, extraClass) {
    var p = region.pts[idx % region.pts.length];
    svg.appendChild(el("circle", {
      cx: p[0], cy: p[1], r: 9, class: "gt-point " + (extraClass || ""),
    }));
    // pulse ring for visibility on the front
    svg.appendChild(el("circle", {
      cx: p[0], cy: p[1], r: 16, class: "gt-point-ring " + (extraClass || ""),
    }));
  }

  function pointFront(root, bundle, target) {
    var region = findRegion(bundle, target);
    // Lean front: the chip carries the task; no redundant headline.
    root.appendChild(chip("Which " + nounOf(bundle) + "?"));

    var built = buildSvg(bundle);
    pointDot(built.svg, region, pointIndex(bundle, target));
    root.appendChild(built.svg);
    root.appendChild(bar("Recall the name, then flip", "gt-hint"));
  }

  function pointBack(root, bundle, target) {
    var region = findRegion(bundle, target);
    root.appendChild(chip("Which " + nounOf(bundle) + "?"));
    root.appendChild(prompt(region.name));

    var built = buildSvg(bundle);
    if (built.byId[target]) built.byId[target].classList.add("gt-answer");
    pointDot(built.svg, region, pointIndex(bundle, target), "gt-on-answer");
    root.appendChild(built.svg);
    root.appendChild(bar("The dot was inside " + region.name, "gt-ok"));
    root.appendChild(bar("Grade yourself: did you name it?", "gt-suggest"));
  }

  // ========================= F5: PLACE-THE-PIECE ===============================

  function trayCenter(bundle) {
    // Scope-declared tray wins; else free space in the inset band right of the
    // last inset; else the bottom-right corner.
    if (bundle.tray) return { x: bundle.tray[0], y: bundle.tray[1] };
    var maxX = 0, bandY = null;
    for (var i = 0; i < bundle.frames.length; i++) {
      var f = bundle.frames[i];
      if (f.id === "main") continue;
      maxX = Math.max(maxX, f.rect[0] + f.rect[2]);
      bandY = f.rect[1] + f.rect[3] / 2;
    }
    if (bandY === null) {
      return { x: bundle.view.w - 120, y: bundle.view.h - 80 };
    }
    return { x: (maxX + bundle.view.w) / 2, y: bandY };
  }

  function placeFront(root, bundle, target) {
    var region = findRegion(bundle, target);
    root.appendChild(chip("Place"));
    root.appendChild(prompt(region.name)); // instruction lives in the hint bar only

    var built = buildSvg(bundle);
    var svg = built.svg;
    // De-emphasize the target's real footprint: remove it from the basemap so
    // its hole doesn't give the position away? No — a hole IS a giveaway. Keep
    // the full basemap; the challenge is matching position, like Sheppard's
    // hard mode where the piece floats over a complete map.

    var tray = trayCenter(bundle);
    var start = { x: tray.x - region.c[0], y: tray.y - region.c[1] };
    var piece = el("path", {
      d: ringPath(region.rings),
      class: "gt-piece",
      transform: "translate(" + start.x + "," + start.y + ")",
    });
    svg.appendChild(piece);
    // Tray hint circle under the piece start.
    svg.insertBefore(
      el("circle", { cx: tray.x, cy: tray.y, r: Math.max(30, region.s * 0.7), class: "gt-tray" }),
      piece
    );
    root.appendChild(svg);

    var hint = bar("Drag the shape to where it belongs", "gt-hint");
    root.appendChild(hint);

    var offset = { x: start.x, y: start.y };
    var dragging = false;
    var grabDelta = null;

    function beginDrag(clientX, clientY) {
      var loc = svgPoint(svg, clientX, clientY);
      if (!loc) return;
      dragging = true;
      grabDelta = { x: loc.x - offset.x, y: loc.y - offset.y };
    }

    function moveDrag(clientX, clientY) {
      if (!dragging) return;
      var loc = svgPoint(svg, clientX, clientY);
      if (!loc) return;
      offset = { x: loc.x - grabDelta.x, y: loc.y - grabDelta.y };
      piece.setAttribute("transform", "translate(" + offset.x + "," + offset.y + ")");
    }

    function endDrag() {
      if (!dragging) return;
      dragging = false;
      saveState("place", bundle.scope, target, { dx: offset.x, dy: offset.y });
      hint.textContent = "Adjust if needed · flip to check";
      hint.className = "gt-bar gt-hint gt-placed";
    }

    piece.addEventListener("pointerdown", function (ev) {
      beginDrag(ev.clientX, ev.clientY);
      try { piece.setPointerCapture(ev.pointerId); } catch (e) { /* older webviews */ }
      ev.preventDefault();
    });
    piece.addEventListener("pointermove", function (ev) {
      moveDrag(ev.clientX, ev.clientY);
      if (dragging) ev.preventDefault();
    });
    piece.addEventListener("pointerup", function (ev) {
      endDrag();
      ev.preventDefault();
    });
    // AnkiDroid's WebView intercepts the gesture for its own scroll/gesture
    // system a few moves in and fires pointercancel — but the raw touch stream
    // keeps flowing. So: non-passive touch handlers preventDefault to stop the
    // interception at the source, drive the same drag as a fallback, and
    // pointercancel is deliberately NOT treated as end-of-drag.
    piece.addEventListener("touchstart", function (ev) {
      if (!dragging && ev.touches.length) beginDrag(ev.touches[0].clientX, ev.touches[0].clientY);
      ev.preventDefault();
    }, { passive: false });
    piece.addEventListener("touchmove", function (ev) {
      if (ev.touches.length) moveDrag(ev.touches[0].clientX, ev.touches[0].clientY);
      ev.preventDefault();
    }, { passive: false });
    piece.addEventListener("touchend", function (ev) {
      endDrag();
      ev.preventDefault();
    }, { passive: false });

    saveState("place", bundle.scope, target, null); // clear stale attempt
  }

  function placeBack(root, bundle, target) {
    var region = findRegion(bundle, target);
    var attempt = loadState("place", bundle.scope, target);

    root.appendChild(chip("Place"));
    root.appendChild(prompt(region.name));

    var built = buildSvg(bundle);
    var svg = built.svg;
    if (built.byId[target]) built.byId[target].classList.add("gt-answer");
    if (attempt) {
      svg.appendChild(el("path", {
        d: ringPath(region.rings),
        class: "gt-piece gt-ghost",
        transform: "translate(" + attempt.dx + "," + attempt.dy + ")",
      }));
    }
    root.appendChild(svg);

    if (!attempt) {
      root.appendChild(bar("No placement recorded — this is where it goes", "gt-miss"));
      root.appendChild(bar(suggestFor(0), "gt-suggest"));
      return;
    }
    var offPx = Math.sqrt(attempt.dx * attempt.dx + attempt.dy * attempt.dy);
    var frame = frameById(bundle, region.frame);
    var km = Math.round(offPx * frame.kmPerUnit);
    var quality = offPx <= region.s * 0.35 ? 2 : offPx <= region.s * 0.9 ? 1 : 0;
    var msg =
      quality === 2 ? "Great placement — ~" + km + " km off"
      : quality === 1 ? "Close — ~" + km + " km off"
      : "Off by ~" + km + " km";
    root.appendChild(bar(msg, quality === 2 ? "gt-ok" : quality === 1 ? "gt-close" : "gt-miss"));
    root.appendChild(bar(suggestFor(quality), "gt-suggest"));
  }

  // ========================= F7: TAP-ALL-NEIGHBORS =============================

  function nbState(bundle, target) {
    return loadState("nb", bundle.scope, target) || { found: [], wrong: [] };
  }

  function neighborsFront(root, bundle, target) {
    var region = findRegion(bundle, target);
    var nbs = region.nb || [];
    root.appendChild(chip("Neighbors"));
    root.appendChild(prompt(region.name));

    var built = buildSvg(bundle);
    var svg = built.svg;
    if (built.byId[target]) built.byId[target].classList.add("gt-target");
    root.appendChild(svg);

    var state = { found: [], wrong: [] };
    saveState("nb", bundle.scope, target, state);

    var hint = bar("Tap every bordering " + nounOf(bundle) + " · 0 / " + nbs.length, "gt-hint");
    root.appendChild(hint);

    function refresh() {
      hint.textContent =
        "Tap every bordering " + nounOf(bundle) + " · " + state.found.length + " / " +
        nbs.length + (state.wrong.length ? " · " + state.wrong.length + " wrong" : "");
      hint.className = "gt-bar gt-hint" + (state.found.length === nbs.length ? " gt-placed" : "");
    }

    function tapAt(clientX, clientY) {
      var loc = svgPoint(svg, clientX, clientY);
      if (!loc) return;
      var hit = regionAt(loc.x, loc.y, bundle);
      if (!hit || hit.id === target) return;
      if (nbs.indexOf(hit.id) >= 0) {
        if (state.found.indexOf(hit.id) < 0) {
          state.found.push(hit.id);
          built.byId[hit.id].classList.add("gt-nb-found");
        }
      } else {
        if (state.wrong.indexOf(hit.id) < 0) state.wrong.push(hit.id);
        var p = built.byId[hit.id];
        p.classList.add("gt-nb-wrong");
        setTimeout(function () { p.classList.remove("gt-nb-wrong"); }, 700);
      }
      saveState("nb", bundle.scope, target, state);
      refresh();
    }

    svg.addEventListener("click", function (ev) { tapAt(ev.clientX, ev.clientY); });
    svg.addEventListener("touchend", function (ev) {
      if (ev.changedTouches && ev.changedTouches.length) {
        var t = ev.changedTouches[0];
        tapAt(t.clientX, t.clientY);
        ev.preventDefault();
      }
    }, { passive: false });
  }

  function neighborsBack(root, bundle, target) {
    var region = findRegion(bundle, target);
    var nbs = region.nb || [];
    var state = nbState(bundle, target);

    root.appendChild(chip("Neighbors"));
    root.appendChild(prompt(region.name));

    var built = buildSvg(bundle);
    if (built.byId[target]) built.byId[target].classList.add("gt-target");
    var missed = [];
    for (var i = 0; i < nbs.length; i++) {
      var id = nbs[i];
      if (state.found.indexOf(id) >= 0) {
        built.byId[id].classList.add("gt-nb-found");
      } else {
        built.byId[id].classList.add("gt-nb-missed");
        missed.push((findRegion(bundle, id) || {}).name);
      }
    }
    for (var k = 0; k < state.wrong.length; k++) {
      var w = built.byId[state.wrong[k]];
      if (w) w.classList.add("gt-nb-wrong");
    }
    root.appendChild(built.svg);

    var quality =
      state.found.length === nbs.length && state.wrong.length === 0 ? 2
      : state.found.length * 2 >= nbs.length && state.wrong.length <= 1 ? 1
      : 0;
    var msg = "Found " + state.found.length + " of " + nbs.length;
    if (state.wrong.length) msg += " · " + state.wrong.length + " wrong";
    if (missed.length) msg += " — missed: " + missed.join(", ");
    root.appendChild(bar(msg, quality === 2 ? "gt-ok" : quality === 1 ? "gt-close" : "gt-miss"));
    root.appendChild(bar(suggestFor(quality), "gt-suggest"));
  }

  // ---- boot ---------------------------------------------------------------------

  var MODES = {
    locate: { front: locateFront, back: locateBack },
    point: { front: pointFront, back: pointBack },
    place: { front: placeFront, back: placeBack },
    neighbors: { front: neighborsFront, back: neighborsBack },
  };

  function mount(root) {
    if (!root || root.getAttribute("data-gt-mounted") === "1") return;
    var scope = root.getAttribute("data-scope");
    var target = root.getAttribute("data-target");
    var side = root.getAttribute("data-side") || "front";
    var mode = root.getAttribute("data-mode") || "locate";
    var bundle = window.GT_BUNDLES && window.GT_BUNDLES[scope];
    if (!bundle) return; // bundle script not evaluated yet; boot() retries
    var impl = MODES[mode] || MODES.locate;
    root.setAttribute("data-gt-mounted", "1");
    root.innerHTML = "";
    (side === "back" ? impl.back : impl.front)(root, bundle, target);
  }

  function mountAll() {
    var nodes = document.querySelectorAll(".gt-app:not([data-gt-mounted='1'])");
    for (var i = 0; i < nodes.length; i++) mount(nodes[i]);
  }

  var tries = 0;
  function boot() {
    mountAll();
    var pending = document.querySelectorAll(".gt-app:not([data-gt-mounted='1'])");
    if (pending.length && tries++ < 60) setTimeout(boot, 50);
  }

  window.GeoTrainer = { mount: mount, mountAll: mountAll, _boot: boot, _hash: strHash };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  }
  boot();
})();
