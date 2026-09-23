(function (global) {
  "use strict";

  var EARTH_KM = 6371.0088;
  var STORAGE_PREFIX = "island-globe:attempt:v1:";
  var SPHERE = { type: "Sphere" };

  function randomUnit() {
    if (global.crypto && global.crypto.getRandomValues) {
      var value = new Uint32Array(1);
      global.crypto.getRandomValues(value);
      return value[0] / 4294967296;
    }
    return Math.random();
  }

  function newState(key) {
    return {
      key: key,
      rotation: [randomUnit() * 360 - 180, randomUnit() * 44 - 22, 0],
      guess: null,
      createdAt: Date.now(),
    };
  }

  function loadState(key) {
    try {
      var stored = JSON.parse(global.localStorage.getItem(STORAGE_PREFIX + key) || "null");
      if (stored) return stored;
    } catch (error) {
    }
    return global.__islandGlobeAttempts && global.__islandGlobeAttempts[key] || null;
  }

  function saveState(state) {
    global.__islandGlobeAttempts = global.__islandGlobeAttempts || {};
    global.__islandGlobeAttempts[state.key] = JSON.parse(JSON.stringify(state));
    try {
      global.localStorage.setItem(STORAGE_PREFIX + state.key, JSON.stringify(state));
    } catch (error) {}
  }

  function css(root, name, fallback) {
    var value = global.getComputedStyle(root).getPropertyValue(name).trim();
    return value || fallback;
  }

  function findTarget(bundle, key) {
    return bundle.targets.features.find(function (item) {
      return item.properties.key === key;
    });
  }

  function pointInVisibleHemisphere(projection, lonLat) {
    var center = projection.invert(projection.translate());
    return global.d3.geoDistance(center, lonLat) <= Math.PI / 2 - 0.002;
  }

  function fitEllipseInsideSphere(center, radii, sphereCenter, sphereRadius) {
    function fits(scale) {
      for (var index = 0; index < 64; index += 1) {
        var angle = (Math.PI * 2 * index) / 64;
        var x = center[0] + radii[0] * scale * Math.cos(angle);
        var y = center[1] + radii[1] * scale * Math.sin(angle);
        if (Math.hypot(x - sphereCenter[0], y - sphereCenter[1]) > sphereRadius * 0.975) {
          return false;
        }
      }
      return true;
    }

    var low = 0;
    var high = 1;
    for (var step = 0; step < 18; step += 1) {
      var mid = (low + high) / 2;
      if (fits(mid)) low = mid;
      else high = mid;
    }
    return [Math.max(7, radii[0] * low), Math.max(7, radii[1] * low)];
  }

  function ellipseGuess(projection, center, rawRadii) {
    var radii = fitEllipseInsideSphere(
      center,
      rawRadii,
      projection.translate(),
      projection.scale(),
    );
    var ring = [];
    for (var index = 0; index < 64; index += 1) {
      var angle = (Math.PI * 2 * index) / 64;
      var point = [
        center[0] + radii[0] * Math.cos(angle),
        center[1] + radii[1] * Math.sin(angle),
      ];
      var lonLat = projection.invert(point);
      if (lonLat) ring.push(lonLat);
    }
    ring.push(ring[0]);
    var geometry = { type: "Polygon", coordinates: [ring] };
    if (global.d3.geoArea(geometry) > Math.PI * 2) {
      ring = ring.slice(0, -1).reverse();
      ring.push(ring[0]);
      geometry = { type: "Polygon", coordinates: [ring] };
    }
    return {
      geometry: geometry,
      center: projection.invert(center),
      screen: { center: center, radii: radii, rotation: projection.rotate() },
    };
  }

  function sameRotation(first, second) {
    return first && second && first.every(function (value, index) {
      return Math.abs(value - second[index]) < 0.001;
    });
  }

  function ellipseBox(center, radii) {
    return {
      left: center[0] - radii[0],
      top: center[1] - radii[1],
      right: center[0] + radii[0],
      bottom: center[1] + radii[1],
    };
  }

  function previewFromBox(box) {
    var left = Math.min(box.left, box.right);
    var right = Math.max(box.left, box.right);
    var top = Math.min(box.top, box.bottom);
    var bottom = Math.max(box.top, box.bottom);
    return {
      center: [(left + right) / 2, (top + bottom) / 2],
      radii: [Math.max(7, (right - left) / 2), Math.max(7, (bottom - top) / 2)],
    };
  }

  function ellipseHandles(box) {
    var centerX = (box.left + box.right) / 2;
    var centerY = (box.top + box.bottom) / 2;
    return {
      nw: [box.left, box.top],
      n: [centerX, box.top],
      ne: [box.right, box.top],
      e: [box.right, centerY],
      se: [box.right, box.bottom],
      s: [centerX, box.bottom],
      sw: [box.left, box.bottom],
      w: [box.left, centerY],
    };
  }

  function scorePlacement(target, guess) {
    var properties = target.properties;
    var components = properties.components || [[properties.lon, properties.lat]];
    var covered = components.filter(function (point) {
      return global.d3.geoContains(guess.geometry, point);
    }).length;
    var coverageRatio = covered / components.length;
    var targetCenter = properties.focus || [properties.lon, properties.lat];
    var centerError = global.d3.geoDistance(guess.center, targetCenter) * EARTH_KM;
    var equivalentRadius = Math.sqrt(global.d3.geoArea(guess.geometry) * EARTH_KM * EARTH_KM / Math.PI);
    var expectedRadius = Math.max(180, (properties.extent_km || 0) + 120);
    var footprintRatio = equivalentRadius / expectedRadius;
    var grade = coverageRatio >= 0.6
      && centerError <= Math.max(250, expectedRadius * 0.6)
      && footprintRatio >= 0.35
      && footprintRatio <= 1.65
      ? "Good"
      : coverageRatio >= 0.2
        && centerError <= Math.max(600, expectedRadius * 1.25)
        && footprintRatio >= 0.15
        && footprintRatio <= 2.4
        ? "Hard"
        : "Again";
    var note = "Close. Adjust the ellipse to cover the archipelago without swallowing a large surrounding region.";
    if (coverageRatio < 0.2) {
      note = "Too little of the archipelago is inside the ellipse.";
    } else if (footprintRatio > 2.4) {
      note = "The ellipse is much broader than the archipelago.";
    } else if (footprintRatio < 0.15) {
      note = "The ellipse is too small for the archipelago's extent.";
    } else if (centerError > Math.max(600, expectedRadius * 1.25)) {
      note = "The ellipse is centered too far from the archipelago.";
    }
    return {
      grade: grade,
      covered: covered,
      componentCount: components.length,
      centerError: centerError,
      footprintRatio: footprintRatio,
      note: note,
    };
  }

  function mount(root, bundle) {
    if (!root || root.dataset.globeReady === "true") return null;
    root.dataset.globeReady = "true";

    var side = root.dataset.side;
    var key = root.dataset.key;
    var target = findTarget(bundle, key);
    if (!target) throw new Error("Unknown island key: " + key);

    var state = side === "front" ? newState(key) : loadState(key) || newState(key);
    if (side === "front") saveState(state);

    var canvas = root.querySelector(".ig-canvas");
    var stage = root.querySelector(".ig-stage");
    var context = canvas.getContext("2d");
    var projection = global.d3.geoOrthographic().clipAngle(90).precision(0.25);
    var path = global.d3.geoPath(projection, context);
    var graticule = global.d3.geoGraticule().step([15, 15]).precision(2.5)();
    var equator = parallel(0);
    var tropicNorth = parallel(23.436);
    var tropicSouth = parallel(-23.436);
    var size = 0;
    var pixelRatio = 1;
    var mode = "rotate";
    var pointer = null;
    var preview = null;
    var handleRadius = 11;

    function setupCanvas() {
      size = Math.max(280, Math.round(stage.getBoundingClientRect().width));
      pixelRatio = Math.min(global.devicePixelRatio || 1, 2);
      canvas.width = Math.round(size * pixelRatio);
      canvas.height = Math.round(size * pixelRatio);
      context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
      projection.fitExtent([[13, 13], [size - 13, size - 13]], SPHERE);
      projection.rotate(state.rotation);
    }

    function parallel(latitude) {
      var coordinates = [];
      for (var longitude = -180; longitude <= 180; longitude += 2) {
        coordinates.push([longitude, latitude]);
      }
      return { type: "LineString", coordinates: coordinates };
    }

    function focusPoint() {
      return target.properties.focus || [target.properties.lon, target.properties.lat];
    }

    function drawGeometry(geometry, fill, stroke, width) {
      context.beginPath();
      path(geometry);
      if (fill) {
        context.fillStyle = fill;
        context.fill();
      }
      if (stroke) {
        context.strokeStyle = stroke;
        context.lineWidth = width || 1;
        context.stroke();
      }
    }

    function drawReferenceLine(geometry, stroke, width, dash) {
      context.save();
      context.setLineDash(dash || []);
      drawGeometry(geometry, null, stroke, width);
      context.restore();
    }

    function drawMarker(item, isTarget) {
      var properties = item.properties;
      var lonLat = [properties.lon, properties.lat];
      if (!pointInVisibleHemisphere(projection, lonLat)) return null;
      var point = projection(lonLat);
      var accent = css(root, "--accent", "#c34c35");
      var ink = css(root, "--ink", "#172a32");
      var paper = css(root, "--paper", "#f7f1e5");

      context.beginPath();
      context.arc(point[0], point[1], isTarget ? 6 : 2.7, 0, Math.PI * 2);
      context.fillStyle = isTarget ? accent : ink;
      context.fill();
      if (isTarget) {
        context.strokeStyle = paper;
        context.lineWidth = 2;
        context.stroke();
      }

      return { item: item, isTarget: isTarget, point: point, ink: ink, accent: accent, paper: paper };
    }

    function boxesOverlap(a, b) {
      return !(a.x + a.w + 2 < b.x || b.x + b.w + 2 < a.x || a.y + a.h + 2 < b.y || b.y + b.h + 2 < a.y);
    }

    function drawMarkerLabels(markers) {
      var occupied = markers.map(function (marker) {
        return { x: marker.point[0] - 5, y: marker.point[1] - 5, w: 10, h: 10 };
      });
      markers.sort(function (a, b) {
        if (a.isTarget !== b.isTarget) return a.isTarget ? -1 : 1;
        return a.point[1] - b.point[1];
      });

      markers.forEach(function (marker) {
        var properties = marker.item.properties;
        var fontSize = marker.isTarget ? 11.5 : 8.5;
        context.font = (marker.isTarget ? "700 " : "600 ") + fontSize + "px ui-sans-serif";
        var width = context.measureText(properties.name).width;
        var height = fontSize + 2;
        var x = marker.point[0];
        var y = marker.point[1];
        var candidates = [
          [x + 7, y - 4],
          [x - width - 7, y - 4],
          [x - width / 2, y - 10],
          [x - width / 2, y + height + 8],
          [x + 7, y - 17],
          [x - width - 7, y - 17],
          [x + 7, y + height + 15],
          [x - width - 7, y + height + 15],
          [x - width / 2, y - 25],
          [x - width / 2, y + height + 27],
        ];
        var chosen = null;
        for (var index = 0; index < candidates.length; index += 1) {
          var box = { x: candidates[index][0], y: candidates[index][1] - height, w: width, h: height };
          var inBounds = box.x >= 7 && box.x + box.w <= size - 7 && box.y >= 7 && box.y + box.h <= size - 58;
          if (inBounds && !occupied.some(function (other) { return boxesOverlap(box, other); })) {
            chosen = box;
            break;
          }
        }
        if (!chosen && marker.isTarget) {
          chosen = { x: Math.max(7, Math.min(size - width - 7, x + 7)), y: Math.max(7, y - height - 7), w: width, h: height };
        }
        if (!chosen) return;
        occupied.push(chosen);

        var baseline = chosen.y + height;
      context.textAlign = "left";
      context.textBaseline = "bottom";
      context.lineWidth = 3;
        context.strokeStyle = marker.paper;
        context.strokeText(properties.name, chosen.x, baseline);
        context.fillStyle = marker.isTarget ? marker.accent : marker.ink;
        context.fillText(properties.name, chosen.x, baseline);
      });
    }

    function drawScreenPreview() {
      if (!preview) return;
      context.save();
      context.beginPath();
      context.ellipse(
        preview.center[0],
        preview.center[1],
        preview.radii[0],
        preview.radii[1],
        0,
        0,
        Math.PI * 2,
      );
      context.fillStyle = "rgba(236, 184, 77, 0.24)";
      context.strokeStyle = css(root, "--guess", "#ecb84d");
      context.lineWidth = 3;
      context.fill();
      context.stroke();
      context.restore();
    }

    function currentEllipsePreview() {
      if (preview) return preview;
      if (!state.guess || !state.guess.geometry) return null;
      if (state.guess.screen && sameRotation(state.guess.screen.rotation, state.rotation)) {
        return { center: state.guess.screen.center.slice(), radii: state.guess.screen.radii.slice() };
      }
      var points = state.guess.geometry.coordinates[0].filter(function (lonLat) {
        return pointInVisibleHemisphere(projection, lonLat);
      }).map(function (lonLat) {
        return projection(lonLat);
      });
      if (points.length < 8) return null;
      var xs = points.map(function (point) { return point[0]; });
      var ys = points.map(function (point) { return point[1]; });
      return previewFromBox({
        left: Math.min.apply(null, xs),
        top: Math.min.apply(null, ys),
        right: Math.max.apply(null, xs),
        bottom: Math.max.apply(null, ys),
      });
    }

    function drawEllipseEditor() {
      if (side !== "front" || mode !== "mark") return;
      var editable = currentEllipsePreview();
      if (!editable) return;
      var box = ellipseBox(editable.center, editable.radii);
      var handles = ellipseHandles(box);
      context.save();
      context.setLineDash([5, 4]);
      context.strokeStyle = "rgba(23,42,50,.58)";
      context.lineWidth = 1;
      context.strokeRect(box.left, box.top, box.right - box.left, box.bottom - box.top);
      context.setLineDash([]);
      Object.keys(handles).forEach(function (name) {
        var point = handles[name];
        context.beginPath();
        context.arc(point[0], point[1], 4.5, 0, Math.PI * 2);
        context.fillStyle = css(root, "--paper", "#f7f1e5");
        context.fill();
        context.strokeStyle = css(root, "--guess", "#ecb84d");
        context.lineWidth = 2;
        context.stroke();
      });
      context.restore();
    }

    function draw() {
      context.clearRect(0, 0, size, size);
      projection.rotate(state.rotation);
      drawGeometry(
        SPHERE,
        css(root, "--ocean", "#9bc5cf"),
        css(root, "--line", "rgba(23,42,50,.22)"),
        1.2,
      );
      drawGeometry(graticule, null, "rgba(255,255,255,.24)", 0.65);
      drawReferenceLine(equator, "rgba(255,255,255,.62)", 1.25);
      drawReferenceLine(tropicNorth, "rgba(255,255,255,.42)", 0.9, [4, 4]);
      drawReferenceLine(tropicSouth, "rgba(255,255,255,.42)", 0.9, [4, 4]);

      var land = side === "front" ? bundle.anchors : bundle.land;
      drawGeometry(
        land,
        css(root, side === "front" ? "--land" : "--land-back", "#d6c7a7"),
        css(root, "--line", "rgba(23,42,50,.22)"),
        0.55,
      );

      if (state.guess && state.guess.geometry && !preview) {
        drawGeometry(
          state.guess.geometry,
          "rgba(236,184,77,.28)",
          css(root, "--guess", "#ecb84d"),
          3,
        );
      }
      if (side === "back") {
        drawGeometry(
          bundle.targets,
          "rgba(23,42,50,.46)",
          css(root, "--line", "rgba(23,42,50,.22)"),
          0.45,
        );
        drawGeometry(
          target,
          "rgba(195,76,53,.72)",
          css(root, "--accent", "#c34c35"),
          2.2,
        );
        var islandMarkers = bundle.targets.features.map(function (item) {
          return drawMarker(item, item.properties.key === key);
        }).filter(Boolean);
        drawMarkerLabels(islandMarkers);
      }
      drawScreenPreview();
      drawEllipseEditor();
    }

    function localPoint(event) {
      var rect = canvas.getBoundingClientRect();
      return [event.clientX - rect.left, event.clientY - rect.top];
    }

    function withinSphere(point) {
      var center = projection.translate();
      return Math.hypot(point[0] - center[0], point[1] - center[1]) <= projection.scale();
    }

    function handleAt(point, box) {
      var handles = ellipseHandles(box);
      return Object.keys(handles).find(function (name) {
        return Math.hypot(point[0] - handles[name][0], point[1] - handles[name][1]) <= handleRadius;
      }) || null;
    }

    function insideEllipse(point, editable) {
      var dx = (point[0] - editable.center[0]) / editable.radii[0];
      var dy = (point[1] - editable.center[1]) / editable.radii[1];
      return dx * dx + dy * dy <= 1;
    }

    function movedBox(box, dx, dy) {
      return {
        left: box.left + dx,
        top: box.top + dy,
        right: box.right + dx,
        bottom: box.bottom + dy,
      };
    }

    function resizedBox(box, handle, point) {
      var resized = { left: box.left, top: box.top, right: box.right, bottom: box.bottom };
      if (handle.indexOf("w") >= 0) resized.left = point[0];
      if (handle.indexOf("e") >= 0) resized.right = point[0];
      if (handle.indexOf("n") >= 0) resized.top = point[1];
      if (handle.indexOf("s") >= 0) resized.bottom = point[1];
      return resized;
    }

    function updateCursor(point) {
      if (pointer) return;
      if (mode === "rotate") {
        canvas.style.cursor = "grab";
        return;
      }
      if (mode !== "mark") {
        canvas.style.cursor = "crosshair";
        return;
      }
      var editable = currentEllipsePreview();
      if (!editable) {
        canvas.style.cursor = "crosshair";
        return;
      }
      var handle = handleAt(point, ellipseBox(editable.center, editable.radii));
      var cursors = {
        n: "ns-resize", s: "ns-resize", e: "ew-resize", w: "ew-resize",
        ne: "nesw-resize", sw: "nesw-resize", nw: "nwse-resize", se: "nwse-resize",
      };
      canvas.style.cursor = handle ? cursors[handle] : insideEllipse(point, editable) ? "move" : "crosshair";
    }

    function pointerDown(event) {
      var point = localPoint(event);
      if (!withinSphere(point)) return;
      pointer = {
        id: event.pointerId,
        start: point,
        last: point,
        rotation: state.rotation.slice(),
      };
      canvas.setPointerCapture(event.pointerId);
      if (mode === "mark") {
        var editable = currentEllipsePreview();
        var box = editable ? ellipseBox(editable.center, editable.radii) : null;
        var handle = box ? handleAt(point, box) : null;
        if (handle) {
          pointer.kind = "resize";
          pointer.handle = handle;
          pointer.box = box;
          preview = editable;
        } else if (editable && insideEllipse(point, editable)) {
          pointer.kind = "move";
          pointer.box = box;
          preview = editable;
        } else {
          pointer.kind = "new";
          pointer.box = { left: point[0], top: point[1], right: point[0], bottom: point[1] };
          preview = { center: point, radii: [7, 7] };
        }
      }
      updateCursor(point);
      event.preventDefault();
      event.stopPropagation();
    }

    function pointerMove(event) {
      var point = localPoint(event);
      if (!pointer || pointer.id !== event.pointerId) {
        updateCursor(point);
        return;
      }
      if (mode === "rotate") {
        canvas.style.cursor = "grabbing";
        var dx = point[0] - pointer.start[0];
        var dy = point[1] - pointer.start[1];
        state.rotation = [
          pointer.rotation[0] + dx * 0.45,
          Math.max(-80, Math.min(80, pointer.rotation[1] - dy * 0.32)),
          0,
        ];
        saveState(state);
      } else if (mode === "mark") {
        var editBox = pointer.kind === "move"
          ? movedBox(pointer.box, point[0] - pointer.start[0], point[1] - pointer.start[1])
          : pointer.kind === "resize"
            ? resizedBox(pointer.box, pointer.handle, point)
            : { left: pointer.start[0], top: pointer.start[1], right: point[0], bottom: point[1] };
        preview = previewFromBox(editBox);
      }
      pointer.last = point;
      draw();
      event.preventDefault();
    }

    function pointerUp(event) {
      if (!pointer || pointer.id !== event.pointerId) return;
      if (mode === "mark" && preview) {
        state.guess = ellipseGuess(projection, preview.center, preview.radii);
        preview = null;
        saveState(state);
      }
      if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
      pointer = null;
      updateCursor(localPoint(event));
      draw();
      event.preventDefault();
      event.stopPropagation();
    }

    canvas.addEventListener("pointerdown", pointerDown, { passive: false });
    canvas.addEventListener("pointermove", pointerMove, { passive: false });
    canvas.addEventListener("pointerup", pointerUp, { passive: false });
    canvas.addEventListener("pointercancel", function () {
      pointer = null;
      preview = null;
      draw();
    });

    root.querySelectorAll("[data-mode]").forEach(function (button) {
      button.addEventListener("click", function (event) {
        mode = button.dataset.mode;
        root.dataset.interaction = mode;
        root.querySelectorAll("[data-mode]").forEach(function (candidate) {
          candidate.setAttribute("aria-pressed", String(candidate === button));
        });
        draw();
        event.preventDefault();
        event.stopPropagation();
      });
    });

    var clear = root.querySelector("[data-action='clear']");
    if (clear) {
      clear.addEventListener("click", function (event) {
        state.guess = null;
        preview = null;
        saveState(state);
        draw();
        event.preventDefault();
        event.stopPropagation();
      });
    }

    var focus = root.querySelector("[data-action='focus']");
    if (focus) {
      focus.addEventListener("click", function (event) {
        var point = focusPoint();
        state.rotation = [-point[0], -point[1], 0];
        saveState(state);
        draw();
        event.preventDefault();
        event.stopPropagation();
      });
    }

    setupCanvas();
    root.dataset.interaction = mode;
    canvas.style.cursor = "grab";
    draw();
    root.dataset.islandsShown = side === "back" ? String(bundle.targets.features.length) : "0";
    root.dataset.family = "place";
    root.dataset.graticuleStep = "15";
    root.dataset.referenceGuides = "equator,tropics";
    function renderFeedback(result, grade, metrics, note) {
      result.textContent = "";
      result.dataset.grade = grade.toLowerCase();
      var top = global.document.createElement("div");
      top.className = "ig-result-top";
      var label = global.document.createElement("span");
      label.className = "ig-result-label";
      label.textContent = "Suggested grade";
      var badge = global.document.createElement("strong");
      badge.className = "ig-grade";
      badge.textContent = grade;
      top.appendChild(label);
      top.appendChild(badge);
      result.appendChild(top);

      var grid = global.document.createElement("div");
      grid.className = "ig-metrics";
      metrics.forEach(function (metric) {
        var item = global.document.createElement("div");
        item.className = "ig-metric";
        var value = global.document.createElement("strong");
        value.textContent = metric.value;
        var metricLabel = global.document.createElement("span");
        metricLabel.textContent = metric.label;
        item.appendChild(value);
        item.appendChild(metricLabel);
        grid.appendChild(item);
      });
      result.appendChild(grid);

      if (note) {
        var diagnosis = global.document.createElement("p");
        diagnosis.className = "ig-diagnosis";
        diagnosis.textContent = note;
        result.appendChild(diagnosis);
      }
    }

    if (side === "back") {
      var result = root.querySelector("[data-result]");
      if (!state.guess) {
        result.textContent = "No ellipse was recorded for this attempt.";
      } else {
        var placement = scorePlacement(target, state.guess);
        renderFeedback(result, placement.grade, [
          {
            value: placement.covered + " / " + placement.componentCount,
            label: placement.componentCount === 1 ? "island component covered" : "island components covered",
          },
          {
            value: Math.round(placement.centerError).toLocaleString() + " km",
            label: "center offset",
          },
          {
            value: placement.footprintRatio.toFixed(1) + "×",
            label: "target footprint",
          },
        ], placement.note);
      }
    }

    var controller = {
      draw: draw,
      getState: function () {
        return JSON.parse(JSON.stringify(state));
      },
    };
    global.__islandGlobeState = controller;
    return controller;
  }

  global.IslandGlobe = { mount: mount, scorePlacement: scorePlacement };
})(window);
