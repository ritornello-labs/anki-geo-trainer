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
    // Smallest hit wins: microstate tap-circles overlap their host country
    // (Vatican/San Marino sit on Italy), and a tap on the magnified circle
    // must mean the microstate, not the country underneath.
    var best = null;
    for (var i = 0; i < bundle.regions.length; i++) {
      var reg = bundle.regions[i];
      if (pointInRegion(x, y, reg) && (!best || reg.s < best.s)) best = reg;
    }
    return best;
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

  function buildSvg(bundle, opts) {
    // opts.borderless: render the land as one seamless silhouette (no internal
    // borders, uniform fill, small regions not circled) so the front is a real
    // blank map — you must recall WHERE things are, not match a labelled shape.
    var borderless = opts && opts.borderless;
    var hideSmall = opts && opts.hideSmall;
    var v = bundle.view;
    var svg = el("svg", { viewBox: "0 0 " + v.w + " " + v.h, class: "gt-map", role: "img" });
    svg.appendChild(el("rect", { x: 0, y: 0, width: v.w, height: v.h, class: "gt-ocean" }));

    // Optional instructional scaffold for latitude belts and vertical
    // cross-sections. These guides are context, never the answer geometry.
    if (bundle.guideLines && bundle.guideLines.length) {
      var guides = el("g", { class: "gt-guides" });
      for (var gi = 0; gi < bundle.guideLines.length; gi++) {
        var gl = bundle.guideLines[gi];
        guides.appendChild(el("line", {
          x1: gl[0], y1: gl[1], x2: gl[2], y2: gl[3], class: "gt-guide",
        }));
      }
      svg.appendChild(guides);
    }
    if (bundle.guidePaths && bundle.guidePaths.length) {
      var guidePaths = el("g", { class: "gt-guide-paths" });
      for (var gp = 0; gp < bundle.guidePaths.length; gp++) {
        var guidePath = bundle.guidePaths[gp];
        guidePaths.appendChild(el("path", {
          d: strokePath(guidePath.points || []),
          class: guidePath.className || "gt-guide",
        }));
      }
      svg.appendChild(guidePaths);
    }
    if (bundle.guideLabels && bundle.guideLabels.length) {
      var labels = el("g", { class: "gt-guide-labels" });
      for (var gli = 0; gli < bundle.guideLabels.length; gli++) {
        var label = bundle.guideLabels[gli];
        var text = el("text", { x: label.x, y: label.y, class: "gt-guide-label" });
        text.textContent = label.text;
        labels.appendChild(text);
      }
      svg.appendChild(labels);
    }

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

    var land = el("g", { class: "gt-land" + (borderless ? " gt-borderless" : "") });
    var byId = {};
    // Physical scopes (ranges/deserts): the feature IS the answer, so the
    // borderless front shows only the context continents (drawn above) — the
    // feature polygons aren't rendered. The back (not borderless) reveals them.
    var hideRegions = borderless && bundle.kind === "physical";
    if (!hideRegions) {
      for (var k = 0; k < bundle.regions.length; k++) {
        var reg = bundle.regions[k];
        if (hideSmall && reg.small) continue;
        var cls = "gt-region";
        if (!borderless) {
          if (reg.small) cls += " gt-small";
          if (reg.tier === 2) cls += " gt-tier2";
        }
        var p = el("path", { d: ringPath(reg.rings), class: cls, "data-id": reg.id });
        land.appendChild(p);
        byId[reg.id] = p;
      }
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

    // Borderless: a dot on a blank silhouette — you must recall what's THERE,
    // not read the label off a bordered shape.
    var built = buildSvg(bundle, { borderless: true });
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

    // Borderless basemap: the piece floats over a blank silhouette, so there's
    // no labelled slot to snap it into — you must know where it belongs.
    var built = buildSvg(bundle, { borderless: true });
    var svg = built.svg;

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

  // ===================== F7: TAP-A-SET (neighbors, members) ====================
  // One interaction — "tap every region that belongs to this answer set" — with
  // the set injected by the caller. `neighbors` reads it off the target region;
  // `members` reads an arbitrary list supplied per note, which is what lets a
  // membership drill (which countries are in ASEAN?) reuse this wholesale.
  // A spec is: {key, chip, title, ids, exclude, highlight, instruction, verb}.

  function setOf(scope, target) {
    return (window.GT_SETS || {})[scope + ":" + target] || null;
  }

  function tapSetState(spec, bundle, target) {
    return loadState(spec.key, bundle.scope, target) || { found: [], wrong: [] };
  }

  function tapSetFront(root, bundle, target, spec) {
    root.appendChild(chip(spec.chip));
    root.appendChild(prompt(spec.title));

    var built = buildSvg(bundle);
    var svg = built.svg;
    if (spec.highlight && built.byId[spec.highlight]) {
      built.byId[spec.highlight].classList.add("gt-target");
    }
    root.appendChild(svg);

    var state = { found: [], wrong: [] };
    saveState(spec.key, bundle.scope, target, state);

    var hint = bar(spec.instruction + " · 0 / " + spec.ids.length, "gt-hint");
    root.appendChild(hint);

    function refresh() {
      hint.textContent =
        spec.instruction + " · " + state.found.length + " / " + spec.ids.length +
        (state.wrong.length ? " · " + state.wrong.length + " wrong" : "");
      hint.className =
        "gt-bar gt-hint" + (state.found.length === spec.ids.length ? " gt-placed" : "");
    }

    function tapAt(clientX, clientY) {
      var loc = svgPoint(svg, clientX, clientY);
      if (!loc) return;
      var hit = regionAt(loc.x, loc.y, bundle);
      if (!hit || hit.id === spec.exclude) return;
      if (spec.ids.indexOf(hit.id) >= 0) {
        // Tapping a found region again un-picks it, so a misfire near a border
        // is recoverable; without this the only fix is redoing the card.
        var at = state.found.indexOf(hit.id);
        if (at < 0) {
          state.found.push(hit.id);
          built.byId[hit.id].classList.add("gt-nb-found");
        } else {
          state.found.splice(at, 1);
          built.byId[hit.id].classList.remove("gt-nb-found");
        }
      } else {
        if (state.wrong.indexOf(hit.id) < 0) state.wrong.push(hit.id);
        var p = built.byId[hit.id];
        p.classList.add("gt-nb-wrong");
        setTimeout(function () { p.classList.remove("gt-nb-wrong"); }, 700);
      }
      saveState(spec.key, bundle.scope, target, state);
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

  function tapSetBack(root, bundle, target, spec) {
    var state = tapSetState(spec, bundle, target);

    root.appendChild(chip(spec.chip));
    root.appendChild(prompt(spec.title));

    var built = buildSvg(bundle);
    if (spec.highlight && built.byId[spec.highlight]) {
      built.byId[spec.highlight].classList.add("gt-target");
    }
    var missed = [];
    for (var i = 0; i < spec.ids.length; i++) {
      var id = spec.ids[i];
      var path = built.byId[id];
      if (state.found.indexOf(id) >= 0) {
        if (path) path.classList.add("gt-nb-found");
      } else {
        if (path) path.classList.add("gt-nb-missed");
        missed.push((findRegion(bundle, id) || { name: id }).name);
      }
    }
    var wrongNames = [];
    for (var k = 0; k < state.wrong.length; k++) {
      var w = built.byId[state.wrong[k]];
      if (w) w.classList.add("gt-nb-wrong");
      wrongNames.push((findRegion(bundle, state.wrong[k]) || { name: state.wrong[k] }).name);
    }
    root.appendChild(built.svg);

    // A set is either right or it isn't: full marks demand every member and no
    // false positives. Partial credit exists only to separate "nearly" from
    // "not really" when grading.
    var quality =
      state.found.length === spec.ids.length && state.wrong.length === 0 ? 2
      : state.found.length * 2 >= spec.ids.length && state.wrong.length <= 1 ? 1
      : 0;
    var msg = "Found " + state.found.length + " of " + spec.ids.length;
    if (missed.length) msg += " — missed: " + missed.join(", ");
    if (wrongNames.length) msg += " — wrong: " + wrongNames.join(", ");
    root.appendChild(bar(msg, quality === 2 ? "gt-ok" : quality === 1 ? "gt-close" : "gt-miss"));
    root.appendChild(bar(suggestFor(quality), "gt-suggest"));
  }

  function neighborsSpec(bundle, target) {
    var region = findRegion(bundle, target) || {};
    return {
      key: "nb",
      chip: "Neighbors",
      title: region.name || target,
      ids: region.nb || [],
      exclude: target,
      highlight: target,
      instruction: "Tap every bordering " + nounOf(bundle),
    };
  }

  function membersSpec(bundle, target) {
    var set = setOf(bundle.scope, target) || {};
    return {
      key: "ms",
      chip: set.chip || "Members",
      title: set.name || target,
      ids: set.ids || [],
      exclude: null,
      highlight: null,
      instruction: set.instruction || ("Tap every member " + nounOf(bundle)),
    };
  }

  function neighborsFront(root, bundle, target) {
    tapSetFront(root, bundle, target, neighborsSpec(bundle, target));
  }
  function neighborsBack(root, bundle, target) {
    tapSetBack(root, bundle, target, neighborsSpec(bundle, target));
  }
  function membersFront(root, bundle, target) {
    tapSetFront(root, bundle, target, membersSpec(bundle, target));
  }
  function membersBack(root, bundle, target) {
    tapSetBack(root, bundle, target, membersSpec(bundle, target));
  }

  // ============================ F6: DRAW-THE-SHAPE =============================
  // Each draw note carries its own outline (window.GT_SHAPES["scope:id"]) — no
  // basemap. Front: freehand multi-stroke sketching. Back: true outline vs the
  // drawing, aligned translation/scale-invariantly, scored by symmetric mean
  // nearest-point distance (chamfer) as % of the shape's diagonal.

  function shapeOf(scope, target) {
    return (window.GT_SHAPES || {})[scope + ":" + target] || null;
  }

  function strokePath(pts) {
    var d = "M" + pts[0][0] + " " + pts[0][1];
    for (var i = 1; i < pts.length; i++) d += "L" + pts[i][0] + " " + pts[i][1];
    return d;
  }

  function resampleStrokes(strokes, budget) {
    var total = 0;
    for (var i = 0; i < strokes.length; i++) total += strokes[i].length;
    if (total <= budget) return strokes;
    var out = [];
    for (var s = 0; s < strokes.length; s++) {
      var pts = strokes[s];
      var keep = Math.max(2, Math.round((pts.length / total) * budget));
      var step = (pts.length - 1) / (keep - 1);
      var res = [];
      for (var k = 0; k < keep; k++) {
        var p = pts[Math.round(k * step)];
        res.push([Math.round(p[0] * 10) / 10, Math.round(p[1] * 10) / 10]);
      }
      out.push(res);
    }
    return out;
  }

  function ringPerimeterPoints(rings, n) {
    // Uniform resample along all ring perimeters, longest rings get more points.
    var segs = [], total = 0;
    for (var r = 0; r < rings.length; r++) {
      var ring = rings[r], len = 0;
      for (var i = 1; i < ring.length; i++) {
        len += Math.hypot(ring[i][0] - ring[i - 1][0], ring[i][1] - ring[i - 1][1]);
      }
      segs.push(len);
      total += len;
    }
    var pts = [];
    for (var r2 = 0; r2 < rings.length; r2++) {
      var ring2 = rings[r2];
      var want = Math.max(8, Math.round((segs[r2] / total) * n));
      var step = segs[r2] / want, acc = 0, next = 0;
      for (var i2 = 1; i2 < ring2.length && pts.length < n + 32; i2++) {
        var ax = ring2[i2 - 1][0], ay = ring2[i2 - 1][1];
        var bx = ring2[i2][0], by = ring2[i2][1];
        var seg = Math.hypot(bx - ax, by - ay);
        while (next <= acc + seg && seg > 0) {
          var t = (next - acc) / seg;
          pts.push([ax + (bx - ax) * t, ay + (by - ay) * t]);
          next += step;
        }
        acc += seg;
      }
    }
    return pts;
  }

  function bboxOf(pts) {
    var x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (var i = 0; i < pts.length; i++) {
      var p = pts[i];
      if (p[0] < x0) x0 = p[0];
      if (p[1] < y0) y0 = p[1];
      if (p[0] > x1) x1 = p[0];
      if (p[1] > y1) y1 = p[1];
    }
    return { x: x0, y: y0, w: Math.max(x1 - x0, 1e-6), h: Math.max(y1 - y0, 1e-6) };
  }

  function alignParams(drawnPts, outlinePts) {
    // Translation + uniform-scale invariance: the drawing is judged on FORM.
    // Uniform scale (not per-axis) so a squished France still loses points.
    // Returns an apply() so every stroke maps with the SAME transform (a
    // multi-island shape must stay registered as separate rings, not merged).
    var db = bboxOf(drawnPts), ob = bboxOf(outlinePts);
    var s = Math.min(ob.w / db.w, ob.h / db.h);
    var dcx = db.x + db.w / 2, dcy = db.y + db.h / 2;
    var ocx = ob.x + ob.w / 2, ocy = ob.y + ob.h / 2;
    return {
      apply: function (pts) {
        var out = [];
        for (var i = 0; i < pts.length; i++) {
          out.push([(pts[i][0] - dcx) * s + ocx, (pts[i][1] - dcy) * s + ocy]);
        }
        return out;
      },
    };
  }

  function alignToShape(drawnPts, outlinePts) {
    return alignParams(drawnPts, outlinePts).apply(drawnPts);
  }

  function nearestDists(a, b) {
    var out = [];
    for (var i = 0; i < a.length; i++) {
      var best = Infinity;
      for (var j = 0; j < b.length; j++) {
        var dx = a[i][0] - b[j][0], dy = a[i][1] - b[j][1];
        var d = dx * dx + dy * dy;
        if (d < best) best = d;
      }
      out.push(Math.sqrt(best));
    }
    return out;
  }

  function meanOf(arr) {
    var s = 0;
    for (var i = 0; i < arr.length; i++) s += arr[i];
    return arr.length ? s / arr.length : 0;
  }

  function percentileOf(arr, p) {
    if (!arr.length) return 0;
    var s = arr.slice().sort(function (x, y) { return x - y; });
    var idx = Math.min(s.length - 1, Math.floor(p * (s.length - 1)));
    return s[idx];
  }

  function pointInRing(x, y, ring) {
    // even-odd ray cast
    var inside = false;
    for (var i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      var xi = ring[i][0], yi = ring[i][1], xj = ring[j][0], yj = ring[j][1];
      if (((yi > y) !== (yj > y)) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
    }
    return inside;
  }

  function areaIoU(drawnRings, trueRings, box, grid) {
    // Rasterised intersection-over-union of the drawn shape vs the true shape.
    // Catches "right area/position but wrong shape" — a lazy circle over an
    // angular country overlaps poorly even though its boundary sits nearby.
    // Both sides are even-odd across their rings, so a multi-part outline
    // (archipelago traced as several strokes) and true-shape holes are honoured.
    var inter = 0, uni = 0;
    var stepX = box.w / grid, stepY = box.h / grid;
    for (var gx = 0; gx < grid; gx++) {
      for (var gy = 0; gy < grid; gy++) {
        var x = box.x + (gx + 0.5) * stepX, y = box.y + (gy + 0.5) * stepY;
        var inD = false;
        for (var d = 0; d < drawnRings.length; d++) {
          if (pointInRing(x, y, drawnRings[d])) inD = !inD;
        }
        var inT = false;
        for (var r = 0; r < trueRings.length; r++) {
          if (pointInRing(x, y, trueRings[r])) inT = !inT; // holes toggle
        }
        if (inD || inT) uni++;
        if (inD && inT) inter++;
      }
    }
    return uni ? inter / uni : 0;
  }

  function shapeScore(strokes, shape, alignDrawing) {
    var drawn = [];
    for (var i = 0; i < strokes.length; i++) {
      for (var j = 0; j < strokes[i].length; j++) drawn.push(strokes[i][j]);
    }
    if (drawn.length < 8) return { pct: 100, iou: 0, quality: 0, empty: true };
    var outline = ringPerimeterPoints(shape.rings, 160);
    var align = alignDrawing ? alignParams(drawn, outline) : {
      apply: function (pts) { return pts.slice(); },
    };
    var aligned = align.apply(drawn);
    // Each stroke aligned separately stays a distinct ring, so an archipelago
    // drawn as several strokes keeps its parts for the area overlap below.
    var alignedRings = [];
    for (var k = 0; k < strokes.length; k++) alignedRings.push(align.apply(strokes[k]));
    var outlineBox = bboxOf(outline);
    var diag = Math.hypot(shape.w || outlineBox.w, shape.h || outlineBox.h);

    // (a) Boundary coverage: the WORST-covered part of the true outline (85th
    // percentile of outline→drawing) so skipping a whole bulge is penalised,
    // plus mean stray to punish scribble outside. As % of the shape diagonal.
    var coverage = nearestDists(outline, aligned);
    var stray = nearestDists(aligned, outline);
    var pct = ((0.5 * percentileOf(coverage, 0.85) + 0.3 * meanOf(coverage) + 0.2 * meanOf(stray)) / diag) * 100;

    // (b) Area IoU: overlap of your shape with the true shape (aligned). This is
    // what rejects a "right size, wrong shape" blob — a circle over Algeria has a
    // nearby boundary but a poor IoU. Both must be good to score Good.
    var bb = bboxOf(outline.concat(aligned));
    var iou = areaIoU(alignedRings, shape.rings, bb, 46);

    // Good needs a faithful boundary AND a strong shape match. Calibration on
    // real shapes: an honest freehand trace (even with ~5% jitter) lands at IoU
    // 0.87–0.99, while a lazy "right size, wrong shape" blob — the irregular
    // circle a user draws when not trying — tops out at ~0.75 for any region.
    // The 0.78 Hard gate sits in that empty band, so a circle over Algeria fails
    // to Again while a real attempt stays Good.
    var quality =
      pct < 4.5 && iou >= 0.80 ? 2
      : pct < 9 && iou >= 0.78 ? 1
      : 0;
    return { pct: pct, iou: iou, quality: quality, aligned: aligned };
  }

  function drawScore(strokes, shape) {
    // Blank-canvas Draw judges form only: where and how large the student drew
    // the outline are intentionally ignored.
    return shapeScore(strokes, shape, true);
  }

  function sketchScore(strokes, region) {
    // Contextual Sketch judges the outline in map coordinates. Position and
    // scale matter because the parent map is the scaffold for both.
    return shapeScore(strokes, region, false);
  }

  var GT_CANVAS = 400; // fixed square side for the blank Draw FRONT

  function drawCanvas(shape, square) {
    // The FRONT is a fixed SQUARE for every card (square=true): a shape-shaped
    // canvas leaks the answer's aspect ratio. Scoring is scale/translation
    // invariant, so a uniform square costs nothing. The BACK keeps the shape's
    // own box so the true outline overlays at its real proportions.
    var w = square ? GT_CANVAS : shape.w;
    var h = square ? GT_CANVAS : shape.h;
    var svg = el("svg", {
      viewBox: "0 0 " + w + " " + h,
      class: "gt-map gt-canvas", role: "img",
    });
    svg.appendChild(el("rect", {
      x: 1, y: 1, width: w - 2, height: h - 2, rx: 8, class: "gt-canvas-bg",
    }));
    return svg;
  }

  function button(label) {
    var b = document.createElement("div");
    b.className = "gt-btn";
    b.textContent = label;
    return b;
  }

  function wireTap(elm, fn) {
    elm.addEventListener("click", fn);
    elm.addEventListener("touchend", function (ev) {
      fn();
      ev.preventDefault();
      ev.stopPropagation();
    }, { passive: false });
  }

  // Shared freehand multi-stroke capture on any SVG surface (draw a shape, trace
  // a river). Persists resampled strokes under (mode, scope, target); returns
  // undo/clear so the caller can wire buttons. Same pointer/touch discipline as
  // the drag code: pointercancel ignored, Android pointerdown-before-touchstart
  // orphan cleaned up.
  function attachStrokeCapture(svg, mode, scope, target, strokeClass, isPan, markerId) {
    var strokes = [], paths = [], current = null, currentPath = null, usingTouch = false, multi = false;
    var panActive = isPan || function () { return false; }; // Move-mode drags pan, don't draw
    saveState(mode, scope, target, { strokes: [] });
    svg.style.touchAction = "none"; // we own pinch/pan; the browser must not scroll/zoom

    function persist() {
      saveState(mode, scope, target, { strokes: resampleStrokes(strokes, 240) });
    }
    function begin(x, y) {
      var loc = svgPoint(svg, x, y);
      if (!loc) return;
      current = [[loc.x, loc.y]];
      currentPath = el("path", { class: strokeClass || "gt-stroke", d: strokePath(current) });
      if (markerId) currentPath.setAttribute("marker-end", "url(#" + markerId + ")");
      svg.appendChild(currentPath);
    }
    function extend(x, y) {
      if (!current) return;
      var loc = svgPoint(svg, x, y);
      if (!loc) return;
      var last = current[current.length - 1];
      if (Math.hypot(loc.x - last[0], loc.y - last[1]) < 1.2) return;
      current.push([loc.x, loc.y]);
      currentPath.setAttribute("d", strokePath(current));
    }
    function finish() {
      if (!current) return;
      if (current.length >= 2) {
        strokes.push(current);
        paths.push(currentPath);
        persist();
      } else if (currentPath) {
        svg.removeChild(currentPath);
      }
      current = null;
      currentPath = null;
    }

    svg.addEventListener("pointerdown", function (ev) {
      if (usingTouch || (ev.button && ev.button !== 0)) return; // right button = pan
      if (panActive()) return; // Move mode: this drag pans instead of drawing
      begin(ev.clientX, ev.clientY);
      ev.preventDefault();
    });
    svg.addEventListener("pointermove", function (ev) {
      if (!usingTouch && current) extend(ev.clientX, ev.clientY);
    });
    svg.addEventListener("pointerup", function () {
      if (!usingTouch) finish();
    });
    svg.addEventListener("touchstart", function (ev) {
      if (ev.touches.length > 1) {
        // A second finger means pan/zoom, not draw: abandon any in-progress
        // stroke and let attachPanZoom handle the gesture.
        multi = true;
        if (currentPath) { svg.removeChild(currentPath); current = null; currentPath = null; }
        return;
      }
      if (multi) return; // leftover finger during a multi-touch gesture
      if (panActive()) return; // Move mode: one finger pans instead of drawing
      if (!usingTouch && currentPath) {
        svg.removeChild(currentPath);
        current = null;
        currentPath = null;
      }
      usingTouch = true;
      var t = ev.changedTouches[0];
      begin(t.clientX, t.clientY);
      ev.preventDefault();
    }, { passive: false });
    svg.addEventListener("touchmove", function (ev) {
      if (multi || ev.touches.length > 1) return;
      var t = ev.changedTouches[0];
      extend(t.clientX, t.clientY);
      ev.preventDefault();
    }, { passive: false });
    svg.addEventListener("touchend", function (ev) {
      if (ev.touches.length === 0) multi = false;
      if (!multi) finish();
      ev.preventDefault();
    }, { passive: false });

    return {
      undo: function () {
        if (current) finish();
        var p = paths.pop();
        if (p) svg.removeChild(p);
        strokes.pop();
        persist();
      },
      clear: function () {
        if (current) finish();
        while (paths.length) svg.removeChild(paths.pop());
        strokes.length = 0;
        persist();
      },
    };
  }

  // Pan/zoom on a drawing surface, so fine work (tracing a river on the world
  // map) is doable: +/- buttons zoom around centre, two fingers pinch-zoom and
  // pan, the wheel zooms toward the cursor. A "Move" toggle (panMode) repurposes
  // a one-finger / left-button drag to pan instead of draw, so a zoomed-in phone
  // user can reposition onto (say) South America with a single finger. Only the
  // viewBox changes — svgPoint uses getScreenCTM, so drawn coordinates stay in
  // map space at any zoom.
  function attachPanZoom(svg) {
    var vb = (svg.getAttribute("viewBox") || "0 0 100 100").split(/\s+/).map(Number);
    var HOME = { x: vb[0], y: vb[1], w: vb[2], h: vb[3] };
    var aspect = HOME.h / HOME.w;
    var cur = { x: HOME.x, y: HOME.y, w: HOME.w, h: HOME.h };
    var MIN_W = HOME.w / 8; // deepest zoom-in
    var panMode = false;

    function apply() {
      svg.setAttribute("viewBox", cur.x + " " + cur.y + " " + cur.w + " " + cur.h);
    }
    function clampPan() {
      cur.x = Math.max(HOME.x, Math.min(HOME.x + HOME.w - cur.w, cur.x));
      cur.y = Math.max(HOME.y, Math.min(HOME.y + HOME.h - cur.h, cur.y));
    }
    function zoomAt(clientX, clientY, factor) {
      var rect = svg.getBoundingClientRect();
      if (!rect.width) return;
      var relX = (clientX - rect.left) / rect.width;
      var relY = (clientY - rect.top) / rect.height;
      var fx = cur.x + relX * cur.w, fy = cur.y + relY * cur.h;
      var newW = Math.max(MIN_W, Math.min(HOME.w, cur.w / factor));
      cur.w = newW;
      cur.h = newW * aspect;
      cur.x = fx - relX * cur.w;
      cur.y = fy - relY * cur.h;
      clampPan();
      apply();
    }
    function zoomCentre(factor) {
      var rect = svg.getBoundingClientRect();
      zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, factor);
    }
    function panBy(dxScreen, dyScreen) {
      var rect = svg.getBoundingClientRect();
      if (!rect.width) return;
      cur.x -= dxScreen * (cur.w / rect.width);
      cur.y -= dyScreen * (cur.h / rect.height);
      clampPan();
      apply();
    }

    function twoFinger(ev) {
      var a = ev.touches[0], b = ev.touches[1];
      return {
        mx: (a.clientX + b.clientX) / 2, my: (a.clientY + b.clientY) / 2,
        dist: Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY),
      };
    }
    var pinch = null, touchPan = null;
    svg.addEventListener("touchstart", function (ev) {
      if (ev.touches.length === 2) {
        pinch = twoFinger(ev); touchPan = null; ev.preventDefault();
      } else if (ev.touches.length === 1 && panMode) {
        touchPan = { x: ev.touches[0].clientX, y: ev.touches[0].clientY };
        ev.preventDefault();
      }
    }, { passive: false });
    svg.addEventListener("touchmove", function (ev) {
      if (ev.touches.length === 2 && pinch) {
        var now = twoFinger(ev);
        panBy(now.mx - pinch.mx, now.my - pinch.my);
        if (pinch.dist > 0) zoomAt(now.mx, now.my, now.dist / pinch.dist);
        pinch = now;
        ev.preventDefault();
      } else if (ev.touches.length === 1 && touchPan) {
        var t = ev.touches[0];
        panBy(t.clientX - touchPan.x, t.clientY - touchPan.y);
        touchPan = { x: t.clientX, y: t.clientY };
        ev.preventDefault();
      }
    }, { passive: false });
    svg.addEventListener("touchend", function (ev) {
      if (ev.touches.length < 2) pinch = null;
      if (ev.touches.length === 0) touchPan = null;
    });
    svg.addEventListener("wheel", function (ev) {
      zoomAt(ev.clientX, ev.clientY, ev.deltaY < 0 ? 1.2 : 1 / 1.2);
      ev.preventDefault();
    }, { passive: false });

    // Desktop pan: right-button drag always pans; in Move mode a left drag pans
    // too (otherwise left drag draws). Two-finger drag pans on touch. Suppresses
    // the context menu while panning.
    var panning = null;
    svg.addEventListener("pointerdown", function (ev) {
      if (ev.pointerType === "touch") return; // touch handled by touch* above
      if (ev.button === 2 || (panMode && ev.button === 0)) {
        panning = { x: ev.clientX, y: ev.clientY };
        ev.preventDefault();
      }
    });
    svg.addEventListener("pointermove", function (ev) {
      if (panning) {
        panBy(ev.clientX - panning.x, ev.clientY - panning.y);
        panning = { x: ev.clientX, y: ev.clientY };
      }
    });
    svg.addEventListener("pointerup", function () { panning = null; });
    svg.addEventListener("contextmenu", function (ev) { ev.preventDefault(); });

    return {
      zoomIn: function () { zoomCentre(1.6); },
      zoomOut: function () { zoomCentre(1 / 1.6); },
      isPanMode: function () { return panMode; },
      setPanMode: function (on) { panMode = !!on; },
    };
  }

  // Wrap the canvas so the map controls can float over it (Google-Maps style:
  // a +/- zoom pill and a ✋ pan toggle in the corner) instead of a button row.
  function drawSurface(root, svg, panzoom) {
    var wrap = document.createElement("div");
    // The square Draw canvas gets a wrap that hugs it (so the floating controls
    // sit on the canvas corner, not out in the letterbox margin); the wide
    // river map fills the wrap edge-to-edge.
    wrap.className = "gt-canvas-wrap" + (svg.classList.contains("gt-canvas") ? " gt-wrap-square" : "");
    wrap.appendChild(svg);
    if (panzoom) {
      var ctl = document.createElement("div");
      ctl.className = "gt-mapctl";
      // ✋ pan toggle (drag draws by default; toggled on, a drag pans instead).
      var pan = document.createElement("div");
      pan.className = "gt-ctl gt-move";
      pan.textContent = "✋";
      pan.setAttribute("role", "button");
      pan.setAttribute("aria-label", "Toggle pan");
      wireTap(pan, function () {
        var on = !panzoom.isPanMode();
        panzoom.setPanMode(on);
        pan.classList.toggle("gt-active", on);
      });
      // Stacked +/- zoom pill.
      var zoom = document.createElement("div");
      zoom.className = "gt-zoomctl";
      var zin = document.createElement("div");
      zin.className = "gt-ctl gt-zoom gt-zin";
      zin.textContent = "+";
      var zout = document.createElement("div");
      zout.className = "gt-ctl gt-zoom gt-zout";
      zout.textContent = "−"; // −
      zoom.appendChild(zin);
      zoom.appendChild(zout);
      wireTap(zin, panzoom.zoomIn);
      wireTap(zout, panzoom.zoomOut);
      ctl.appendChild(pan);
      ctl.appendChild(zoom);
      wrap.appendChild(ctl);
    }
    root.appendChild(wrap);
    return wrap;
  }

  function drawToolRow(root, surface) {
    var row = document.createElement("div");
    row.className = "gt-btnrow";
    var undo = button("Undo"), clear = button("Clear");
    row.appendChild(undo);
    row.appendChild(clear);
    root.appendChild(row);
    wireTap(undo, surface.undo);
    wireTap(clear, surface.clear);
  }

  // ======================== CONTEXTUAL SKETCH-THE-SHAPE =======================
  // An easier bridge between Place and blank-canvas Draw. The front supplies a
  // borderless parent map (continent for countries, country for subdivisions),
  // but no internal boundaries. The student sketches the named region in place;
  // the back reveals the boundaries and grades shape + position + scale directly.

  function sketchFront(root, bundle, target) {
    var region = findRegion(bundle, target);
    root.appendChild(chip("Sketch"));
    root.appendChild(prompt(region ? region.name : target));
    if (!region) {
      root.appendChild(bar("Region data missing", "gt-miss"));
      return;
    }

    // Magnified microstate circles are tap affordances, not geography. Sketch
    // omits them from the blank front so they do not look like stray islands.
    var built = buildSvg(bundle, { borderless: true, hideSmall: true });
    var svg = built.svg;
    svg.classList.add("gt-sketch-map");
    var panzoom = attachPanZoom(svg);
    var surface = attachStrokeCapture(
      svg, "sketch", bundle.scope, target, "gt-stroke", panzoom.isPanMode
    );
    drawSurface(root, svg, panzoom);
    drawToolRow(root, surface);
    root.appendChild(bar("Sketch it in place on the blank map, then flip", "gt-hint"));
  }

  function sketchBack(root, bundle, target) {
    var region = findRegion(bundle, target);
    root.appendChild(chip("Sketch"));
    root.appendChild(prompt(region ? region.name : target));
    if (!region) {
      root.appendChild(bar("Region data missing", "gt-miss"));
      return;
    }

    var built = buildSvg(bundle);
    var svg = built.svg;
    svg.classList.add("gt-sketch-map");
    if (built.byId[target]) built.byId[target].classList.add("gt-answer");

    var state = loadState("sketch", bundle.scope, target);
    var strokes = (state && state.strokes) || [];
    for (var i = 0; i < strokes.length; i++) {
      if (strokes[i].length >= 2) {
        svg.appendChild(el("path", { class: "gt-drawn", d: strokePath(strokes[i]) }));
      }
    }
    root.appendChild(svg);

    var score = sketchScore(strokes, region);
    if (score.empty) {
      root.appendChild(bar("No sketch recorded — this is where it goes", "gt-miss"));
      root.appendChild(bar(suggestFor(0), "gt-suggest"));
      return;
    }

    var offset = Math.round(score.pct * 10) / 10;
    var msg =
      score.quality === 2 ? "Solid map sketch — average offset " + offset + "% of size"
      : score.quality === 1 ? "Recognizable in place — average offset " + offset + "% of size"
      : "Keep practicing shape and position — average offset " + offset + "% of size";
    root.appendChild(bar(msg, score.quality === 2 ? "gt-ok" : score.quality === 1 ? "gt-close" : "gt-miss"));
    root.appendChild(bar(suggestFor(score.quality), "gt-suggest"));
  }

  function drawFront(root, bundle, target) {
    var shape = shapeOf(bundle.scope, target);
    root.appendChild(chip("Draw"));
    root.appendChild(prompt(root.getAttribute("data-name") || target));
    if (!shape) {
      root.appendChild(bar("Shape data missing", "gt-miss"));
      return;
    }
    var svg = drawCanvas(shape, true); // fixed square front — no aspect hint
    var panzoom = attachPanZoom(svg);
    var surface = attachStrokeCapture(svg, "draw", bundle.scope, target, "gt-stroke", panzoom.isPanMode);
    drawSurface(root, svg, panzoom);
    drawToolRow(root, surface);
    root.appendChild(bar("Draw the outline from memory, then flip", "gt-hint"));
  }

  function drawBack(root, bundle, target) {
    var shape = shapeOf(bundle.scope, target);
    root.appendChild(chip("Draw"));
    root.appendChild(prompt(root.getAttribute("data-name") || target));
    if (!shape) {
      root.appendChild(bar("Shape data missing", "gt-miss"));
      return;
    }

    var svg = drawCanvas(shape);
    svg.appendChild(el("path", { class: "gt-outline", d: ringPath(shape.rings) }));
    root.appendChild(svg);

    var state = loadState("draw", bundle.scope, target);
    var strokes = (state && state.strokes) || [];
    var score = drawScore(strokes, shape);
    if (score.empty) {
      root.appendChild(bar("No drawing recorded", "gt-miss"));
      root.appendChild(bar(suggestFor(0), "gt-suggest"));
      return;
    }

    // Overlay the drawing in the same alignment the score used.
    var flat = [];
    for (var i = 0; i < strokes.length; i++) flat = flat.concat(strokes[i]);
    var outline = ringPerimeterPoints(shape.rings, 160);
    var db = bboxOf(flat), ob = bboxOf(outline);
    var s = Math.min(ob.w / db.w, ob.h / db.h);
    var dcx = db.x + db.w / 2, dcy = db.y + db.h / 2;
    var ocx = ob.x + ob.w / 2, ocy = ob.y + ob.h / 2;
    for (var k = 0; k < strokes.length; k++) {
      var mapped = [];
      for (var m = 0; m < strokes[k].length; m++) {
        mapped.push([
          (strokes[k][m][0] - dcx) * s + ocx,
          (strokes[k][m][1] - dcy) * s + ocy,
        ]);
      }
      if (mapped.length >= 2) {
        svg.appendChild(el("path", { class: "gt-drawn", d: strokePath(mapped) }));
      }
    }

    var offset = Math.round(score.pct * 10) / 10;
    var msg =
      score.quality === 2 ? "Solid outline — average offset " + offset + "% of size"
      : score.quality === 1 ? "Recognizable — average offset " + offset + "% of size"
      : "Keep practicing — average offset " + offset + "% of size";
    root.appendChild(bar(msg, score.quality === 2 ? "gt-ok" : score.quality === 1 ? "gt-close" : "gt-miss"));
    root.appendChild(bar(suggestFor(score.quality), "gt-suggest"));
  }

  // ============================ F8: CAPITAL-LOCATE =============================
  // "Tap where <Capital> is." The target is a POINT (the capital's projected
  // location), carried per-note in data-cappt; graded by distance like a locate
  // miss. The region map is the same basemap the other families use.

  function capitalPoint(root) {
    var raw = (root.getAttribute("data-cappt") || "").split(",");
    if (raw.length < 2) return null;
    var x = parseFloat(raw[0]), y = parseFloat(raw[1]);
    return isNaN(x) || isNaN(y) ? null : { x: x, y: y };
  }

  function capitalFront(root, bundle, target) {
    var capName = root.getAttribute("data-capname") || "the capital";
    root.appendChild(chip("Capital"));
    root.appendChild(prompt(capName));

    var built = buildSvg(bundle);
    var svg = built.svg;
    var marker = el("circle", { r: 9, class: "gt-attempt", style: "display:none" });
    svg.appendChild(marker);
    root.appendChild(svg);

    var hint = bar("Tap where " + capName + " is", "gt-hint");
    root.appendChild(hint);
    saveState("capital", bundle.scope, target, null);

    function place(clientX, clientY) {
      var loc = svgPoint(svg, clientX, clientY);
      if (!loc) return;
      marker.setAttribute("cx", loc.x);
      marker.setAttribute("cy", loc.y);
      marker.style.display = "";
      saveState("capital", bundle.scope, target, { x: loc.x, y: loc.y });
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
  }

  function capitalStar(cx, cy) {
    // Five-point star marking the true capital.
    var pts = [];
    for (var i = 0; i < 10; i++) {
      var r = i % 2 === 0 ? 11 : 4.6;
      var a = -Math.PI / 2 + (i * Math.PI) / 5;
      pts.push(cx + r * Math.cos(a) + "," + (cy + r * Math.sin(a)));
    }
    return el("polygon", { points: pts.join(" "), class: "gt-capital" });
  }

  function capitalBack(root, bundle, target) {
    var capName = root.getAttribute("data-capname") || "the capital";
    var truth = capitalPoint(root);
    var region = findRegion(bundle, target);
    var attempt = loadState("capital", bundle.scope, target);

    root.appendChild(chip("Capital"));
    root.appendChild(prompt(capName));

    var built = buildSvg(bundle);
    var svg = built.svg;
    if (built.byId[target]) built.byId[target].classList.add("gt-answer");

    var km = null;
    if (attempt && truth) {
      var fa = frameOf(bundle, attempt.x, attempt.y);
      var ft = frameOf(bundle, truth.x, truth.y);
      km = kmBetween(bundle, attempt.x, attempt.y, truth.x, truth.y, fa, ft);
      if (attempt.x !== truth.x || attempt.y !== truth.y) {
        svg.appendChild(el("line", {
          x1: attempt.x, y1: attempt.y, x2: truth.x, y2: truth.y, class: "gt-link",
        }));
      }
      svg.appendChild(el("circle", { cx: attempt.x, cy: attempt.y, r: 8, class: "gt-attempt gt-bad" }));
    }
    if (truth) svg.appendChild(capitalStar(truth.x, truth.y));
    root.appendChild(svg);

    var where = region ? " (" + region.name + ")" : "";
    if (!attempt) {
      root.appendChild(bar("No tap recorded — " + capName + " is starred" + where, "gt-miss"));
      root.appendChild(bar(suggestFor(0), "gt-suggest"));
      return;
    }
    var quality = km === null ? 0 : km < 150 ? 2 : km < 500 ? 1 : 0;
    var msg = km === null
      ? capName + " is starred" + where
      : (km < 60 ? "Spot on — " : "Off by ~" + km + " km — ") + capName + where;
    root.appendChild(bar(msg, quality === 2 ? "gt-ok" : quality === 1 ? "gt-close" : "gt-miss"));
    root.appendChild(bar(suggestFor(quality), "gt-suggest"));
  }

  // ============================ F9: RIVER-LOCATE ==============================
  // Rivers are lines. The base bundle carries only world land context; each
  // river's polyline comes per-note via GT_SHAPES[scope:id] = {name, paths}.
  // "Tap where the <River> is", graded by distance to the nearest point on it.

  function riverData(scope, target) {
    return (window.GT_SHAPES || {})[scope + ":" + target] || null;
  }

  function pointToSegment(px, py, ax, ay, bx, by) {
    var dx = bx - ax, dy = by - ay;
    var len2 = dx * dx + dy * dy;
    var t = len2 ? ((px - ax) * dx + (py - ay) * dy) / len2 : 0;
    t = t < 0 ? 0 : t > 1 ? 1 : t;
    var cx = ax + t * dx, cy = ay + t * dy;
    return Math.hypot(px - cx, py - cy);
  }

  function distToRiver(px, py, paths) {
    var best = Infinity;
    for (var i = 0; i < paths.length; i++) {
      var p = paths[i];
      for (var j = 1; j < p.length; j++) {
        var d = pointToSegment(px, py, p[j - 1][0], p[j - 1][1], p[j][0], p[j][1]);
        if (d < best) best = d;
      }
    }
    return best;
  }

  function riverPaths(svg, paths, cls) {
    for (var i = 0; i < paths.length; i++) {
      if (paths[i].length >= 2) {
        svg.appendChild(el("path", { d: strokePath(paths[i]), class: cls }));
      }
    }
  }

  function addArrowMarker(svg, id, cls) {
    var defs = el("defs");
    var marker = el("marker", {
      id: id,
      viewBox: "0 0 10 10",
      refX: "8.2",
      refY: "5",
      markerWidth: "4",
      markerHeight: "4",
      orient: "auto-start-reverse",
      markerUnits: "strokeWidth",
    });
    marker.appendChild(el("path", { d: "M 0 0 L 10 5 L 0 10 z", class: cls }));
    defs.appendChild(marker);
    svg.insertBefore(defs, svg.firstChild);
  }

  function directedPaths(svg, paths, cls, markerId) {
    for (var i = 0; i < paths.length; i++) {
      if (paths[i].length >= 2) {
        svg.appendChild(el("path", {
          d: strokePath(paths[i]),
          class: cls,
          "marker-end": "url(#" + markerId + ")",
        }));
      }
    }
  }

  function riverTargetPoints(paths) {
    var pts = [];
    for (var i = 0; i < paths.length; i++) {
      for (var j = 0; j < paths[i].length; j++) pts.push(paths[i][j]);
    }
    return pts;
  }

  // Trace-the-course scoring: direct chamfer (NO alignment — you must draw the
  // river where it actually runs), graded in real KM via the map's kmPerUnit.
  // The percentile-coverage penalty makes skipping a whole reach fail; km scale
  // is intuitive and doesn't blow up for long thin rivers (a bbox-relative % did).
  function riverScore(strokes, paths, kmPerUnit) {
    var drawn = [];
    for (var i = 0; i < strokes.length; i++) {
      for (var j = 0; j < strokes[i].length; j++) drawn.push(strokes[i][j]);
    }
    if (drawn.length < 8) return { km: null, quality: 0, empty: true };
    var target = riverTargetPoints(paths);
    var coverage = nearestDists(target, drawn); // reach you missed
    var stray = nearestDists(drawn, target);     // where you strayed
    var px = 0.5 * percentileOf(coverage, 0.85) + 0.3 * meanOf(coverage) + 0.2 * meanOf(stray);
    var km = Math.round(px * (kmPerUnit || 1));
    // Freehand at world scale: within ~250 km of the course = Good, ~650 = Hard.
    var quality = km < 250 ? 2 : km < 650 ? 1 : 0;
    return { km: km, quality: quality };
  }

  function riverFront(root, bundle, target) {
    var data = riverData(bundle.scope, target);
    var name = data ? data.name : target;
    root.appendChild(chip("Trace"));
    root.appendChild(prompt(name));

    // The world map (land context, no river drawn) is the drawing surface — you
    // trace the river's course over the continents where you think it runs.
    var built = buildSvg(bundle);
    var svg = built.svg;
    // Zoom/pan so you can dive into the region and trace the line precisely,
    // even though the front starts on the full world map (no positional hint).
    var panzoom = attachPanZoom(svg);
    var surface = attachStrokeCapture(svg, "river", bundle.scope, target, "gt-drawn", panzoom.isPanMode);
    drawSurface(root, svg, panzoom);
    drawToolRow(root, surface);
    root.appendChild(bar("Zoom in (＋), tap ✋ to reposition, then trace the " + name, "gt-hint"));
  }

  function riverBack(root, bundle, target) {
    var data = riverData(bundle.scope, target);
    var name = data ? data.name : target;
    var state = loadState("river", bundle.scope, target);
    var strokes = (state && state.strokes) || [];

    root.appendChild(chip("Trace"));
    root.appendChild(prompt(name));

    var built = buildSvg(bundle);
    var svg = built.svg;
    if (data) riverPaths(svg, data.paths, "gt-river"); // the true course
    for (var k = 0; k < strokes.length; k++) {
      if (strokes[k].length >= 2) {
        svg.appendChild(el("path", { class: "gt-drawn", d: strokePath(strokes[k]) }));
      }
    }
    root.appendChild(svg);

    var frame = frameById(bundle, "main");
    var score = data ? riverScore(strokes, data.paths, frame ? frame.kmPerUnit : 1)
      : { quality: 0, empty: true };
    if (score.empty) {
      root.appendChild(bar("Nothing traced — the " + name + " is highlighted", "gt-miss"));
      root.appendChild(bar(suggestFor(0), "gt-suggest"));
      return;
    }
    var msg =
      score.quality === 2 ? "Good course (~" + score.km + " km off) — the " + name
      : score.quality === 1 ? "Roughly right (~" + score.km + " km off) — the " + name
      : "Off course (~" + score.km + " km) — the " + name + " is highlighted";
    root.appendChild(bar(msg, score.quality === 2 ? "gt-ok" : score.quality === 1 ? "gt-close" : "gt-miss"));
    root.appendChild(bar(suggestFor(score.quality), "gt-suggest"));
  }

  // ==================== DIRECTION-AWARE OCEAN-CURRENT TRACE ===================
  // Current routes use the river tracing surface, but their ordered endpoints
  // matter: a geographically accurate line drawn backwards is still wrong.

  function longestPath(paths) {
    var best = [];
    for (var i = 0; i < paths.length; i++) {
      if (paths[i].length > best.length) best = paths[i];
    }
    return best;
  }

  function endpointDistance(a, b) {
    return Math.hypot(a[0] - b[0], a[1] - b[1]);
  }

  function currentScore(strokes, paths, kmPerUnit) {
    var drawn = [];
    for (var i = 0; i < strokes.length; i++) {
      for (var j = 0; j < strokes[i].length; j++) drawn.push(strokes[i][j]);
    }
    if (drawn.length < 8) return { km: null, quality: 0, empty: true, reversed: false };

    var target = riverTargetPoints(paths);
    var coverage = nearestDists(target, drawn);
    var stray = nearestDists(drawn, target);
    var px = 0.5 * percentileOf(coverage, 0.85) + 0.3 * meanOf(coverage) + 0.2 * meanOf(stray);
    var km = Math.round(px * (kmPerUnit || 1));

    var trace = longestPath(strokes);
    var route = longestPath(paths);
    var reversed = false;
    if (trace.length >= 2 && route.length >= 2) {
      var forward = endpointDistance(trace[0], route[0])
        + endpointDistance(trace[trace.length - 1], route[route.length - 1]);
      var backward = endpointDistance(trace[0], route[route.length - 1])
        + endpointDistance(trace[trace.length - 1], route[0]);
      reversed = backward < forward;
    }

    // Routes are schematic corridors on a full-world map, so tolerate more
    // positional error than the detailed Natural Earth river polylines.
    var quality = reversed ? 0 : km < 500 ? 2 : km < 1000 ? 1 : 0;
    return { km: km, quality: quality, reversed: reversed };
  }

  // Prevailing winds and jets occupy broad latitude belts. A learner may draw
  // a representative arrow anywhere in the belt, so scoring against one fixed
  // longitude corridor would create false failures. Grade latitude, direction,
  // and a minimally useful stroke length instead.
  function atmosphericBandScore(strokes, data) {
    var trace = longestPath(strokes);
    if (!trace || trace.length < 2) {
      return { offset: null, quality: 0, empty: true, reversed: false };
    }
    var first = trace[0], last = trace[trace.length - 1];
    var dx = last[0] - first[0], dy = last[1] - first[1];
    var length = Math.sqrt(dx * dx + dy * dy);
    if (length < 35) return { offset: null, quality: 0, empty: true, reversed: false };

    var expected = data.directionVector || [1, 0];
    var expectedLength = Math.sqrt(expected[0] * expected[0] + expected[1] * expected[1]) || 1;
    var cosine = (dx * expected[0] + dy * expected[1]) / (length * expectedLength);
    var reversed = cosine < 0;
    var band = data.acceptBand || [0, Infinity];
    var outside = [];
    for (var i = 0; i < trace.length; i++) {
      var y = trace[i][1];
      outside.push(y < band[0] ? band[0] - y : y > band[1] ? y - band[1] : 0);
    }
    var offset = meanOf(outside);
    var quality = reversed ? 0
      : cosine >= 0.55 && offset <= 12 ? 2
      : cosine >= 0.15 && offset <= 42 ? 1
      : 0;
    return {
      offset: Math.round(offset), quality: quality, empty: false,
      reversed: reversed, cosine: cosine,
    };
  }

  function atmosphericRouteScore(strokes, paths, kmPerUnit) {
    var result = currentScore(strokes, paths, kmPerUnit);
    if (!result.empty && !result.reversed) {
      result.quality = result.km < 1200 ? 2 : result.km < 2400 ? 1 : 0;
    }
    return result;
  }

  // Latitude–depth sections use plot coordinates rather than map kilometres.
  // Keep the open-route direction check from currentScore, but calibrate the
  // corridor in pixels so a trace must occupy the correct depth as well as the
  // correct latitude range.
  function sectionScore(strokes, paths) {
    var drawn = [];
    for (var i = 0; i < strokes.length; i++) {
      for (var j = 0; j < strokes[i].length; j++) drawn.push(strokes[i][j]);
    }
    if (drawn.length < 8) return { offset: null, quality: 0, empty: true, reversed: false };

    var target = riverTargetPoints(paths);
    var coverage = nearestDists(target, drawn);
    var stray = nearestDists(drawn, target);
    var offset = 0.5 * percentileOf(coverage, 0.85)
      + 0.3 * meanOf(coverage) + 0.2 * meanOf(stray);

    var trace = longestPath(strokes);
    var route = longestPath(paths);
    var reversed = false;
    if (trace.length >= 2 && route.length >= 2) {
      var forward = endpointDistance(trace[0], route[0])
        + endpointDistance(trace[trace.length - 1], route[route.length - 1]);
      var backward = endpointDistance(trace[0], route[route.length - 1])
        + endpointDistance(trace[trace.length - 1], route[0]);
      reversed = backward < forward;
    }
    var quality = reversed ? 0 : offset < 28 ? 2 : offset < 65 ? 1 : 0;
    return { offset: Math.round(offset), quality: quality, reversed: reversed };
  }

  function closestPointIndex(point, route) {
    var best = 0, dist = Infinity;
    for (var i = 0; i < route.length; i++) {
      var d = endpointDistance(point, route[i]);
      if (d < dist) { dist = d; best = i; }
    }
    return best;
  }

  // A circulation cell is a closed loop, so endpoints cannot distinguish
  // forward from reverse. Project the learner's stroke onto a dense ordered
  // loop and accumulate wrapped index movement instead.
  function singleCellScore(stroke, path) {
    var drawn = [];
    for (var i = 0; i < stroke.length; i++) drawn.push(stroke[i]);
    if (drawn.length < 8) return { offset: null, quality: 0, empty: true, reversed: false };

    var target = riverTargetPoints([path]);
    var coverage = nearestDists(target, drawn);
    var stray = nearestDists(drawn, target);
    var offset = 0.5 * percentileOf(coverage, 0.85) + 0.3 * meanOf(coverage) + 0.2 * meanOf(stray);

    var route = ringPerimeterPoints([path], 220);
    var trace = stroke;
    var total = 0, previous = null;
    for (var k = 0; k < trace.length; k += Math.max(1, Math.floor(trace.length / 80))) {
      var idx = closestPointIndex(trace[k], route);
      if (previous !== null) {
        var delta = idx - previous;
        if (delta > route.length / 2) delta -= route.length;
        if (delta < -route.length / 2) delta += route.length;
        total += delta;
      }
      previous = idx;
    }
    var reversed = total < 0;
    var quality = reversed ? 0 : offset < 26 ? 2 : offset < 58 ? 1 : 0;
    return { offset: Math.round(offset), quality: quality, reversed: reversed };
  }

  function cellScore(strokes, paths) {
    var usable = [];
    for (var i = 0; i < strokes.length; i++) {
      if (strokes[i].length >= 8) usable.push(strokes[i]);
    }
    if (!usable.length) return { offset: null, quality: 0, empty: true, reversed: false };
    if (paths.length === 1) return singleCellScore(longestPath(usable), paths[0]);
    if (usable.length < paths.length) {
      return { offset: null, quality: 0, empty: false, reversed: false, incomplete: true };
    }

    // The paired-cell cards have two target loops. Try both assignments so the
    // learner may draw the hemispheres in either order.
    var a0 = singleCellScore(usable[0], paths[0]);
    var a1 = singleCellScore(usable[1], paths[1]);
    var b0 = singleCellScore(usable[0], paths[1]);
    var b1 = singleCellScore(usable[1], paths[0]);
    var scoreA = a0.quality + a1.quality;
    var scoreB = b0.quality + b1.quality;
    var chosen = scoreB > scoreA ? [b0, b1] : [a0, a1];
    return {
      offset: Math.round((chosen[0].offset + chosen[1].offset) / 2),
      quality: Math.min(chosen[0].quality, chosen[1].quality),
      empty: false,
      reversed: chosen[0].reversed || chosen[1].reversed,
    };
  }

  function traceSpec(mode) {
    var specs = {
      current: {
        chip: "Trace current",
        hint: "Trace from origin to destination — your arrow shows direction",
        good: "Good route and direction",
        rough: "Rough route, correct direction",
        off: "Off route",
      },
      seasonalcurrent: {
        chip: "Trace seasonal current",
        hint: "Trace the route for the named season — your arrow shows direction",
        good: "Good seasonal route and direction",
        rough: "Rough seasonal route, correct direction",
        off: "Off seasonal route",
      },
      wind: {
        chip: "Trace prevailing wind",
        hint: "Draw a representative arrow inside the correct latitude belt",
        good: "Good wind belt and direction",
        rough: "Rough wind belt, correct direction",
        off: "Off wind belt",
      },
      seasonalwind: {
        chip: "Trace seasonal wind",
        hint: "Trace the flow for the named season — your arrow shows direction",
        good: "Good seasonal wind and direction",
        rough: "Rough seasonal wind, correct direction",
        off: "Off seasonal wind route",
      },
      jet: {
        chip: "Trace jet stream",
        hint: "Trace the broad west-to-east corridor — a schematic meander is enough",
        good: "Good jet corridor and direction",
        rough: "Rough jet corridor, correct direction",
        off: "Off jet corridor",
      },
      cell: {
        chip: "Trace circulation cell",
        hint: "Start at both dots and trace the paired loops in the direction air moves",
        good: "Good circulation loop and direction",
        rough: "Rough circulation loop, correct direction",
        off: "Off circulation loop",
      },
      amoc: {
        chip: "Trace Atlantic overturning",
        hint: "Start at the dot and trace the flow through latitude and depth",
        good: "Good depth pathway and direction",
        rough: "Rough depth pathway, correct direction",
        off: "Off depth pathway",
      },
    };
    return specs[mode] || specs.current;
  }

  function directedTraceFront(root, bundle, target, mode) {
    var data = riverData(bundle.scope, target);
    var name = data ? data.name : target;
    var spec = traceSpec(mode);
    root.appendChild(chip(spec.chip));
    root.appendChild(prompt(name));
    if (data && data.season) {
      root.appendChild(bar(data.season, "gt-season"));
    }

    var built = buildSvg(bundle);
    var svg = built.svg;
    var markerId = "gt-user-" + mode + "-arrow";
    addArrowMarker(svg, markerId, "gt-current-user-arrow");
    if (mode === "cell" && data && data.paths.length) {
      for (var pi = 0; pi < data.paths.length; pi++) {
        if (data.paths[pi].length) {
          svg.appendChild(el("circle", {
            cx: data.paths[pi][0][0], cy: data.paths[pi][0][1], r: 8,
            class: "gt-flow-start",
          }));
        }
      }
    }
    var panzoom = mode === "cell" ? null : attachPanZoom(svg);
    var surface = attachStrokeCapture(
      svg, mode, bundle.scope, target, "gt-current-user",
      panzoom ? panzoom.isPanMode : function () { return false; }, markerId
    );
    if (panzoom) drawSurface(root, svg, panzoom);
    else root.appendChild(svg);
    drawToolRow(root, surface);
    root.appendChild(bar(spec.hint, "gt-hint"));
  }

  function directedTraceBack(root, bundle, target, mode) {
    var data = riverData(bundle.scope, target);
    var name = data ? data.name : target;
    var state = loadState(mode, bundle.scope, target);
    var strokes = (state && state.strokes) || [];
    var spec = traceSpec(mode);

    root.appendChild(chip(spec.chip));
    root.appendChild(prompt(name));
    if (data && data.season) {
      root.appendChild(bar(data.season, "gt-season"));
    }
    var built = buildSvg(bundle);
    var svg = built.svg;
    var targetMarker = "gt-target-" + mode + "-arrow";
    var userMarker = "gt-user-" + mode + "-arrow";
    var variant = (data && (data.temperature || data.style)) || "neutral";
    addArrowMarker(svg, targetMarker, "gt-current-arrow gt-current-arrow-" + variant);
    addArrowMarker(svg, userMarker, "gt-current-user-arrow");
    if (data) {
      if ((mode === "wind" || mode === "jet") && data.acceptBand) {
        svg.appendChild(el("rect", {
          x: 0, y: data.acceptBand[0], width: bundle.view.w,
          height: data.acceptBand[1] - data.acceptBand[0], class: "gt-flow-band",
        }));
      }
      riverPaths(svg, data.paths, "gt-current-corridor");
      directedPaths(svg, data.paths, "gt-current gt-current-" + variant, targetMarker);
    }
    for (var k = 0; k < strokes.length; k++) {
      if (strokes[k].length >= 2) {
        svg.appendChild(el("path", {
          class: "gt-current-user",
          d: strokePath(strokes[k]),
          "marker-end": "url(#" + userMarker + ")",
        }));
      }
    }
    root.appendChild(svg);

    var frame = frameById(bundle, "main");
    var score = data
      ? (mode === "cell"
        ? cellScore(strokes, data.paths)
        : mode === "wind" || mode === "jet"
          ? atmosphericBandScore(strokes, data)
          : mode === "seasonalwind"
            ? atmosphericRouteScore(strokes, data.paths, frame ? frame.kmPerUnit : 1)
            : currentScore(strokes, data.paths, frame ? frame.kmPerUnit : 1))
      : { quality: 0, empty: true, reversed: false };
    if (score.empty) {
      root.appendChild(bar("Nothing traced — the directed route is highlighted", "gt-miss"));
      root.appendChild(bar(suggestFor(0), "gt-suggest"));
      return;
    }
    if (score.reversed) {
      root.appendChild(bar(
        "Right corridor, reversed direction — follow the highlighted arrow",
        "gt-miss"
      ));
      root.appendChild(bar(suggestFor(0), "gt-suggest"));
      return;
    }
    if (score.incomplete) {
      root.appendChild(bar("Trace both hemispheric cells before flipping", "gt-miss"));
      root.appendChild(bar(suggestFor(0), "gt-suggest"));
      return;
    }
    var distance = mode === "current" || mode === "seasonalcurrent"
      ? " (~" + score.km + " km off)"
      : "";
    var msg =
      score.quality === 2 ? spec.good + distance
      : score.quality === 1 ? spec.rough + distance
      : spec.off + distance + " — follow the highlighted arrow";
    root.appendChild(bar(
      msg,
      score.quality === 2 ? "gt-ok" : score.quality === 1 ? "gt-close" : "gt-miss"
    ));
    root.appendChild(bar(suggestFor(score.quality), "gt-suggest"));
  }

  function currentFront(root, bundle, target) {
    directedTraceFront(root, bundle, target, "current");
  }

  function currentBack(root, bundle, target) {
    directedTraceBack(root, bundle, target, "current");
  }

  function seasonalCurrentFront(root, bundle, target) { directedTraceFront(root, bundle, target, "seasonalcurrent"); }
  function seasonalCurrentBack(root, bundle, target) { directedTraceBack(root, bundle, target, "seasonalcurrent"); }
  function windFront(root, bundle, target) { directedTraceFront(root, bundle, target, "wind"); }
  function windBack(root, bundle, target) { directedTraceBack(root, bundle, target, "wind"); }
  function seasonalWindFront(root, bundle, target) { directedTraceFront(root, bundle, target, "seasonalwind"); }
  function seasonalWindBack(root, bundle, target) { directedTraceBack(root, bundle, target, "seasonalwind"); }
  function jetFront(root, bundle, target) { directedTraceFront(root, bundle, target, "jet"); }
  function jetBack(root, bundle, target) { directedTraceBack(root, bundle, target, "jet"); }
  function cellFront(root, bundle, target) { directedTraceFront(root, bundle, target, "cell"); }
  function cellBack(root, bundle, target) { directedTraceBack(root, bundle, target, "cell"); }

  function svgText(svg, x, y, textValue, cls, anchor) {
    var textNode = el("text", {
      x: x, y: y, class: cls || "gt-diagram-label",
      "text-anchor": anchor || "start",
    });
    textNode.textContent = textValue;
    svg.appendChild(textNode);
    return textNode;
  }

  function drawAmocZones(svg) {
    svg.appendChild(el("rect", { x: 90, y: 62, width: 860, height: 145, class: "gt-amoc-upper-zone" }));
    svg.appendChild(el("rect", { x: 90, y: 250, width: 860, height: 190, class: "gt-amoc-deep-zone" }));
    svgText(svg, 925, 192, "upper ocean", "gt-amoc-zone-label", "end");
    svgText(svg, 925, 430, "deep ocean", "gt-amoc-zone-label", "end");
  }

  function drawAmocAnswer(svg, data, numbered) {
    var segments = (data && data.segments) || [];
    for (var i = 0; i < segments.length; i++) {
      var markerId = "gt-amoc-segment-" + i;
      addArrowMarker(svg, markerId, "gt-current-arrow gt-current-arrow-" + segments[i].style);
      directedPaths(svg, [segments[i].path], "gt-current gt-current-" + segments[i].style, markerId);
    }
    if (numbered && data && data.waypoints) {
      for (var k = 0; k < data.waypoints.length; k++) {
        var waypoint = data.waypoints[k];
        svg.appendChild(el("circle", {
          cx: waypoint.point[0], cy: waypoint.point[1], r: 15, class: "gt-amoc-waypoint-answer",
        }));
        svgText(svg, waypoint.point[0], waypoint.point[1] + 5, String(k + 1),
          "gt-amoc-waypoint-number", "middle");
        var labelY = waypoint.point[1] + (k < 2 ? -25 : 34);
        svgText(svg, waypoint.point[0], labelY, waypoint.label,
          "gt-amoc-waypoint-label", k === 0 || k === 3 ? "start" : "end");
      }
    }
  }

  function amocDirectionFront(root, bundle, target, data) {
    root.appendChild(chip("Atlantic overturning directions"));
    root.appendChild(prompt(data.name));
    var built = buildSvg(bundle);
    drawAmocZones(built.svg);
    root.appendChild(built.svg);

    var state = { upper: null, deep: null };
    saveState("amoc", bundle.scope, target, state);
    var choices = document.createElement("div");
    choices.className = "gt-choice-grid";
    var specs = [
      { key: "upper", label: "Upper-ocean limb" },
      { key: "deep", label: "Deep return limb" },
    ];
    for (var i = 0; i < specs.length; i++) {
      (function (spec) {
        var row = document.createElement("div");
        row.className = "gt-choice-row";
        var label = document.createElement("div");
        label.className = "gt-choice-label";
        label.textContent = spec.label;
        row.appendChild(label);
        var north = button("Northward");
        var south = button("Southward");
        row.appendChild(north);
        row.appendChild(south);
        function select(value) {
          state[spec.key] = value;
          north.classList.toggle("gt-selected", value === "northward");
          south.classList.toggle("gt-selected", value === "southward");
          saveState("amoc", bundle.scope, target, state);
        }
        wireTap(north, function () { select("northward"); });
        wireTap(south, function () { select("southward"); });
        choices.appendChild(row);
      })(specs[i]);
    }
    root.appendChild(choices);
    root.appendChild(bar("Choose one direction for each limb, then flip", "gt-hint"));
  }

  function amocSequenceFront(root, bundle, target, data) {
    root.appendChild(chip("Order Atlantic overturning"));
    root.appendChild(prompt(data.name));
    var built = buildSvg(bundle);
    var svg = built.svg;
    drawAmocZones(svg);
    root.appendChild(svg);
    var order = [];
    var markers = [];
    saveState("amoc", bundle.scope, target, { order: order });

    function refresh() {
      saveState("amoc", bundle.scope, target, { order: order });
    }
    function place(clientX, clientY) {
      var loc = svgPoint(svg, clientX, clientY);
      if (!loc) return;
      var best = 0, bestDistance = Infinity;
      for (var i = 0; i < data.waypoints.length; i++) {
        var p = data.waypoints[i].point;
        var distance = endpointDistance([loc.x, loc.y], p);
        if (distance < bestDistance) { bestDistance = distance; best = i; }
      }
      order.push(best);
      var marker = el("g", { class: "gt-amoc-attempt-marker" });
      marker.appendChild(el("circle", { cx: loc.x, cy: loc.y, r: 14, class: "gt-attempt" }));
      var number = el("text", {
        x: loc.x, y: loc.y + 5, class: "gt-amoc-attempt-number", "text-anchor": "middle",
      });
      number.textContent = String(order.length);
      marker.appendChild(number);
      svg.appendChild(marker);
      markers.push(marker);
      refresh();
    }
    svg.addEventListener("click", function (ev) { place(ev.clientX, ev.clientY); });
    svg.addEventListener("touchend", function (ev) {
      if (ev.changedTouches && ev.changedTouches.length) {
        place(ev.changedTouches[0].clientX, ev.changedTouches[0].clientY);
        ev.preventDefault();
      }
    }, { passive: false });
    var row = document.createElement("div");
    row.className = "gt-btnrow";
    var undo = button("Undo");
    var clear = button("Clear");
    row.appendChild(undo);
    row.appendChild(clear);
    root.appendChild(row);
    wireTap(undo, function () {
      if (!order.length) return;
      order.pop();
      var marker = markers.pop();
      if (marker && marker.parentNode) marker.parentNode.removeChild(marker);
      refresh();
    });
    wireTap(clear, function () {
      order = [];
      for (var i = 0; i < markers.length; i++) {
        if (markers[i].parentNode) markers[i].parentNode.removeChild(markers[i]);
      }
      markers = [];
      refresh();
    });
    root.appendChild(bar("Tap each stage in pathway order; flip when complete", "gt-hint"));
  }

  function amocFront(root, bundle, target) {
    var data = riverData(bundle.scope, target);
    if (data && data.interaction === "sequence") {
      amocSequenceFront(root, bundle, target, data);
    } else {
      amocDirectionFront(root, bundle, target, data || { name: target });
    }
  }

  function amocBack(root, bundle, target) {
    var data = riverData(bundle.scope, target);
    var state = loadState("amoc", bundle.scope, target) || {};
    var sequence = data && data.interaction === "sequence";
    root.appendChild(chip(sequence ? "Order Atlantic overturning" : "Atlantic overturning directions"));
    root.appendChild(prompt(data ? data.name : target));
    var built = buildSvg(bundle);
    drawAmocZones(built.svg);
    drawAmocAnswer(built.svg, data, sequence);
    root.appendChild(built.svg);

    if (sequence) {
      var order = state.order || [];
      var expected = [0, 1, 2, 3];
      var exact = order.length === expected.length;
      var prefix = 0;
      for (var i = 0; i < Math.min(order.length, expected.length); i++) {
        if (order[i] !== expected[i]) { exact = false; break; }
        prefix += 1;
      }
      var quality = exact ? 2 : prefix >= 2 ? 1 : 0;
      var msg = exact
        ? "Correct: upper south → upper north → deep north → deep south"
        : "Follow the numbered upper, sinking, and deep-return pathway";
      root.appendChild(bar(msg, quality === 2 ? "gt-ok" : quality === 1 ? "gt-close" : "gt-miss"));
      root.appendChild(bar(suggestFor(quality), "gt-suggest"));
      return;
    }

    var upperCorrect = state.upper === "northward";
    var deepCorrect = state.deep === "southward";
    var correctCount = (upperCorrect ? 1 : 0) + (deepCorrect ? 1 : 0);
    var directionQuality = correctCount === 2 ? 2 : correctCount === 1 ? 1 : 0;
    root.appendChild(bar(
      "Upper ocean: northward · deep return: southward",
      directionQuality === 2 ? "gt-ok" : directionQuality === 1 ? "gt-close" : "gt-miss"
    ));
    root.appendChild(bar(suggestFor(directionQuality), "gt-suggest"));
  }

  function ensoFrame(svg, x, y, width, height, title) {
    svg.appendChild(el("rect", { x: x, y: y, width: width, height: height, rx: 12, class: "gt-enso-panel" }));
    svg.appendChild(el("rect", { x: x + 18, y: y + 48, width: 42, height: 116, class: "gt-enso-land" }));
    svg.appendChild(el("rect", { x: x + width - 60, y: y + 48, width: 42, height: 116, class: "gt-enso-land" }));
    svgText(svg, x + width / 2, y + 28, title || "equatorial Pacific", "gt-enso-title", "middle");
    svgText(svg, x + 38, y + 180, "Indonesia", "gt-enso-place", "middle");
    svgText(svg, x + width - 38, y + 180, "Americas", "gt-enso-place", "middle");
    svg.appendChild(el("line", {
      x1: x + 60, y1: y + 202, x2: x + width - 60, y2: y + 202, class: "gt-enso-surface",
    }));
    return { x: x, y: y, width: width, height: height };
  }

  function drawEnsoState(svg, state, box, compact) {
    var oceanLeft = box.x + 60, oceanRight = box.x + box.width - 60;
    var oceanWidth = oceanRight - oceanLeft;
    var planY = box.y + 105;
    var warmX = oceanLeft + state.warmCenter * oceanWidth;
    svg.appendChild(el("ellipse", {
      cx: warmX, cy: planY, rx: Math.max(28, state.warmWidth * oceanWidth / 2),
      ry: compact ? 19 : 27, class: "gt-enso-warm-pool",
    }));
    var windId = "gt-enso-wind-" + state.state + "-" + Math.round(box.x);
    addArrowMarker(svg, windId, "gt-enso-wind-arrow");
    var windPath = [[oceanLeft + oceanWidth * 0.78, box.y + 75], [oceanLeft + oceanWidth * 0.30, box.y + 75]];
    svg.appendChild(el("path", {
      d: strokePath(windPath),
      class: "gt-enso-wind gt-enso-wind-" + state.windStrength,
      "marker-end": "url(#" + windId + ")",
    }));
    svgText(svg, oceanLeft + oceanWidth * state.rainCenter, box.y + 137, "rain",
      "gt-enso-rain", "middle");

    var crossTop = box.y + 202, crossBottom = box.y + box.height - 28;
    var westDepth = crossTop + state.thermocline[0] * (crossBottom - crossTop);
    var eastDepth = crossTop + state.thermocline[1] * (crossBottom - crossTop);
    svg.appendChild(el("path", {
      d: "M" + oceanLeft + "," + westDepth + " L" + oceanRight + "," + eastDepth,
      class: "gt-enso-thermocline",
    }));
    var upId = "gt-enso-up-" + state.state + "-" + Math.round(box.x);
    addArrowMarker(svg, upId, "gt-enso-upwelling-arrow");
    svg.appendChild(el("path", {
      d: "M" + (oceanRight - 18) + "," + (crossTop + 65) + " L" + (oceanRight - 18) + "," + (crossTop + 12),
      class: "gt-enso-upwelling gt-enso-upwelling-" + state.upwelling,
      "marker-end": "url(#" + upId + ")",
    }));
    if (!compact) {
      svgText(svg, oceanLeft + 10, westDepth + 24, "thermocline", "gt-enso-label", "start");
      svgText(svg, oceanRight - 25, crossTop + 82, state.upwelling + " upwelling", "gt-enso-label", "end");
      svgText(svg, oceanLeft + oceanWidth * 0.54, box.y + 67,
        state.windStrength + " easterly trades", "gt-enso-label", "middle");
    }
  }

  function ensoFront(root, bundle, target) {
    var data = riverData(bundle.scope, target);
    root.appendChild(chip("Recall ENSO pattern"));
    root.appendChild(prompt(data ? data.name : target));
    var built = buildSvg(bundle);
    if (data && data.state === "comparison") {
      var titles = ["ENSO-neutral", "El Niño", "La Niña"];
      for (var i = 0; i < 3; i++) ensoFrame(built.svg, 20 + i * 325, 70, 305, 425, titles[i]);
    } else {
      ensoFrame(built.svg, 90, 45, 820, 485, "equatorial Pacific");
    }
    root.appendChild(built.svg);
    root.appendChild(bar(
      data && data.state === "comparison"
        ? "Compare the trades, warm water, upwelling, rainfall, and thermocline"
        : "Recall the trades, warm water, upwelling, rainfall, and thermocline",
      "gt-hint"
    ));
  }

  function ensoBack(root, bundle, target) {
    var data = riverData(bundle.scope, target);
    root.appendChild(chip("Recall ENSO pattern"));
    root.appendChild(prompt(data ? data.name : target));
    var built = buildSvg(bundle);
    if (data && data.state === "comparison") {
      var titles = ["ENSO-neutral", "El Niño", "La Niña"];
      for (var i = 0; i < data.states.length; i++) {
        var box = ensoFrame(built.svg, 20 + i * 325, 70, 305, 425, titles[i]);
        drawEnsoState(built.svg, data.states[i], box, true);
      }
    } else if (data) {
      var stateBox = ensoFrame(built.svg, 90, 45, 820, 485, "equatorial Pacific");
      drawEnsoState(built.svg, data, stateBox, false);
    }
    root.appendChild(built.svg);
    root.appendChild(bar("Grade yourself: did you recall the coupled pattern?", "gt-suggest"));
  }

  function beltScore(taps, bands) {
    if (!taps || !bands || taps.length !== bands.length) {
      return { quality: 0, empty: !taps || !taps.length, maxOffset: null };
    }
    var unused = bands.slice();
    var maxOffset = 0;
    for (var i = 0; i < taps.length; i++) {
      var y = taps[i].y;
      var best = -1, bestOffset = Infinity;
      for (var j = 0; j < unused.length; j++) {
        var rect = unused[j];
        var top = rect[1], bottom = rect[1] + rect[3];
        var offset = y < top ? top - y : y > bottom ? y - bottom : 0;
        if (offset < bestOffset) { bestOffset = offset; best = j; }
      }
      maxOffset = Math.max(maxOffset, bestOffset);
      unused.splice(best, 1);
    }
    return {
      maxOffset: Math.round(maxOffset),
      quality: maxOffset === 0 ? 2 : maxOffset < 34 ? 1 : 0,
      empty: false,
    };
  }

  function beltFront(root, bundle, target) {
    var data = riverData(bundle.scope, target);
    var bands = (data && data.bands) || [];
    root.appendChild(chip("Place pressure belt"));
    root.appendChild(prompt(data ? data.name : target));
    var built = buildSvg(bundle);
    var svg = built.svg;
    var taps = [];
    var markers = [];
    root.appendChild(svg);
    var hint = bar("Tap each latitude band where it belongs", "gt-hint");
    root.appendChild(hint);
    var row = document.createElement("div");
    row.className = "gt-btnrow";
    var undo = button("Undo");
    var clear = button("Clear");
    row.appendChild(undo);
    row.appendChild(clear);
    root.appendChild(row);
    saveState("belt", bundle.scope, target, { taps: [] });

    function refresh() {
      hint.textContent = taps.length
        ? "Markers placed · flip when you think every band is marked"
        : "Tap every latitude band where it belongs";
      hint.className = "gt-bar gt-hint" + (taps.length ? " gt-placed" : "");
      saveState("belt", bundle.scope, target, { taps: taps });
    }
    function place(clientX, clientY) {
      var loc = svgPoint(svg, clientX, clientY);
      if (!loc) return;
      taps.push({ x: loc.x, y: loc.y });
      var marker = el("circle", { cx: loc.x, cy: loc.y, r: 9, class: "gt-attempt" });
      markers.push(marker);
      svg.appendChild(marker);
      refresh();
    }
    svg.addEventListener("click", function (ev) { place(ev.clientX, ev.clientY); });
    svg.addEventListener("touchend", function (ev) {
      if (ev.changedTouches && ev.changedTouches.length) {
        place(ev.changedTouches[0].clientX, ev.changedTouches[0].clientY);
        ev.preventDefault();
      }
    }, { passive: false });
    wireTap(undo, function () {
      if (!taps.length) return;
      taps.pop();
      var marker = markers.pop();
      if (marker && marker.parentNode) marker.parentNode.removeChild(marker);
      refresh();
    });
    wireTap(clear, function () {
      taps = [];
      for (var i = 0; i < markers.length; i++) {
        if (markers[i].parentNode) markers[i].parentNode.removeChild(markers[i]);
      }
      markers = [];
      refresh();
    });
  }

  function beltBack(root, bundle, target) {
    var data = riverData(bundle.scope, target);
    var bands = (data && data.bands) || [];
    var state = loadState("belt", bundle.scope, target);
    var taps = (state && state.taps) || [];
    root.appendChild(chip("Place pressure belt"));
    root.appendChild(prompt(data ? data.name : target));
    var built = buildSvg(bundle);
    var svg = built.svg;
    for (var i = 0; i < bands.length; i++) {
      svg.appendChild(el("rect", {
        x: bands[i][0], y: bands[i][1], width: bands[i][2], height: bands[i][3],
        class: "gt-belt-target",
      }));
    }
    for (var j = 0; j < taps.length; j++) {
      svg.appendChild(el("circle", {
        cx: taps[j].x, cy: taps[j].y, r: 9, class: "gt-attempt",
      }));
    }
    root.appendChild(svg);
    var score = beltScore(taps, bands);
    var msg = score.empty
      ? "No belts placed — the answer bands are highlighted"
      : score.quality === 2
        ? "All pressure belts placed correctly"
        : score.quality === 1
          ? "Close to the correct latitude bands"
          : "One or more belts are at the wrong latitude";
    root.appendChild(bar(msg, score.quality === 2 ? "gt-ok" : score.quality === 1 ? "gt-close" : "gt-miss"));
    root.appendChild(bar(suggestFor(score.quality), "gt-suggest"));
  }

  // ---- boot ---------------------------------------------------------------------

  // neighbors stays dormant: the family was retired from the packs (2026-07-05,
  // duplicates the user's existing borders decks) but the mode remains valid.
  var MODES = {
    locate: { front: locateFront, back: locateBack },
    point: { front: pointFront, back: pointBack },
    place: { front: placeFront, back: placeBack },
    sketch: { front: sketchFront, back: sketchBack },
    neighbors: { front: neighborsFront, back: neighborsBack },
    // members: same tap-a-set interaction, answer list injected per note via
    // GT_SETS[scope:target] — needsSet gates mounting on that script arriving.
    members: { front: membersFront, back: membersBack, needsSet: true },
    // selfContained: no basemap bundle (draw carries its own outline).
    // needsShape: also requires GT_SHAPES[scope:id] before mounting.
    draw: { front: drawFront, back: drawBack, selfContained: true, needsShape: true },
    capital: { front: capitalFront, back: capitalBack },
    river: { front: riverFront, back: riverBack, needsShape: true },
    current: { front: currentFront, back: currentBack, needsShape: true },
    seasonalcurrent: { front: seasonalCurrentFront, back: seasonalCurrentBack, needsShape: true },
    wind: { front: windFront, back: windBack, needsShape: true },
    seasonalwind: { front: seasonalWindFront, back: seasonalWindBack, needsShape: true },
    jet: { front: jetFront, back: jetBack, needsShape: true },
    cell: { front: cellFront, back: cellBack, needsShape: true },
    amoc: { front: amocFront, back: amocBack, needsShape: true },
    enso: { front: ensoFront, back: ensoBack, needsShape: true },
    belt: { front: beltFront, back: beltBack, needsShape: true },
  };

  function mount(root) {
    if (!root || root.getAttribute("data-gt-mounted") === "1") return;
    var scope = root.getAttribute("data-scope");
    var target = root.getAttribute("data-target");
    var side = root.getAttribute("data-side") || "front";
    var mode = root.getAttribute("data-mode") || "locate";
    var impl = MODES[mode] || MODES.locate;
    var bundle;
    if (impl.selfContained) {
      // Draw cards carry their own outline per note; no basemap bundle.
      if (!shapeOf(scope, target)) return; // shape script not evaluated yet
      bundle = { scope: scope };
    } else {
      bundle = window.GT_BUNDLES && window.GT_BUNDLES[scope];
      if (!bundle) return; // bundle script not evaluated yet; boot() retries
      if (impl.needsShape && !shapeOf(scope, target)) return; // per-note data not ready
      if (impl.needsSet && !setOf(scope, target)) return; // answer-set script not ready
    }
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
    // Keep polling until at least one app has mounted (the card HTML or the
    // bundle script may arrive AFTER this engine evaluates — scripts load
    // async and out of order on AnkiMobile/AnkiDroid), then until nothing is
    // pending. A zero-pending page with no mounts yet is "too early", not done.
    var pending = document.querySelectorAll(".gt-app:not([data-gt-mounted='1'])");
    var mounted = document.querySelector(".gt-app[data-gt-mounted='1']");
    if ((pending.length || !mounted) && tries++ < 120) setTimeout(boot, 50);
  }

  window.GeoTrainer = {
    mount: mount, mountAll: mountAll, _boot: boot, _hash: strHash,
    _drawScore: drawScore, // exposed for tests: scoring must be verifiable headlessly
    _sketchScore: sketchScore,
    _riverScore: riverScore,
    _currentScore: currentScore,
    _atmosphericBandScore: atmosphericBandScore,
    _atmosphericRouteScore: atmosphericRouteScore,
    _cellScore: cellScore,
    _sectionScore: sectionScore,
    _beltScore: beltScore,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  }
  boot();
})();
