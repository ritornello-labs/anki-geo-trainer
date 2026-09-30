(function (global) {
  "use strict";

  var PREFIX = "reference-lines-time-qa:v2:";
  var SPHERE = { type: "Sphere" };

  function decode(value) {
    var binary = global.atob(value);
    var bytes = Uint8Array.from(binary, function (character) { return character.charCodeAt(0); });
    return JSON.parse(new TextDecoder().decode(bytes));
  }

  function save(key, state) {
    global.__referenceQaAttempts = global.__referenceQaAttempts || {};
    global.__referenceQaAttempts[key] = JSON.parse(JSON.stringify(state));
    try { global.localStorage.setItem(PREFIX + key, JSON.stringify(state)); } catch (error) {}
  }

  function load(key) {
    try {
      var stored = JSON.parse(global.localStorage.getItem(PREFIX + key) || "null");
      if (stored) return stored;
    } catch (error) {}
    return global.__referenceQaAttempts && global.__referenceQaAttempts[key] || null;
  }

  function element(tag, className, text) {
    var node = global.document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function color(root, name, fallback) {
    return global.getComputedStyle(root).getPropertyValue(name).trim() || fallback;
  }

  function randomUnit() {
    if (global.crypto && global.crypto.getRandomValues) {
      var value = new Uint32Array(1);
      global.crypto.getRandomValues(value);
      return value[0] / 4294967296;
    }
    return Math.random();
  }

  function chooseClockSample(draw) {
    var random = draw || randomUnit;
    var forward = random() < .5;
    var rollover = random() < .5;
    var low = forward ? (rollover ? 21 : 0) : (rollover ? 0 : 3);
    var high = forward ? (rollover ? 23 : 20) : (rollover ? 2 : 23);
    return {
      from: forward ? "UTC−3" : "UTC",
      to: forward ? "UTC" : "UTC−3",
      fromOffset: forward ? -3 : 0,
      toOffset: forward ? 0 : -3,
      hour: low + Math.floor(random() * (high - low + 1)),
    };
  }

  function angleError(axis, guess, target) {
    var delta = Math.abs(guess - target);
    return axis === "lon" ? Math.min(delta, 360 - delta) : delta;
  }

  function clockAnswer(data) {
    var total = data.hour - data.fromOffset + data.toOffset;
    var day = Math.floor(total / 24);
    return { hour: ((total % 24) + 24) % 24, day: day };
  }

  function dayLabel(day) {
    return day < 0 ? "previous day" : day > 0 ? "next day" : "same day";
  }

  function degreeLabel(axis, value) {
    var abs = Math.abs(value);
    if (axis === "lon" && abs > 179.5) return "180°";
    if (abs < 0.25) return "0°";
    return abs.toFixed(1).replace(".0", "") + "° " +
      (axis === "lat" ? (value > 0 ? "N" : "S") : (value > 0 ? "E" : "W"));
  }

  function lineGeometry(axis, value) {
    var points = [];
    var position;
    if (axis === "lat") {
      for (position = -180; position <= 180; position += 2) points.push([position, value]);
    } else {
      for (position = -89.9; position <= 89.9; position += 2) points.push([value, position]);
    }
    return { type: "LineString", coordinates: points };
  }

  function mountFigure(root, data, side, bundle) {
    if (!data.figure) return;
    var host = root.querySelector(".rq-interaction");
    var figure = element("div", "rq-figure");
    var title = data.figure === "tropical-belt" ? "The tropical belt" :
      data.figure === "polar-circles" ? "The polar regions" :
      "Pacific-centred view near 180°";
    if (data.figure === "tropical-belt" || data.figure === "polar-circles") {
      var tropical = data.figure === "tropical-belt";
      figure.innerHTML = '<svg viewBox="0 0 480 190" role="img" aria-label="' + title + '">' +
        '<defs><clipPath id="rq-earth-clip"><circle cx="240" cy="95" r="77"/></clipPath></defs>' +
        '<rect width="480" height="190" fill="#b8d9df"/>' +
        '<circle cx="240" cy="95" r="77" fill="#e9dfca" stroke="#637d80" stroke-width="2"/>' +
        '<g clip-path="url(#rq-earth-clip)">' +
        (tropical ? '<rect x="160" y="75" width="160" height="40" fill="#eab394" opacity=".85"/>' :
          '<rect x="160" y="18" width="160" height="20" fill="#eab394" opacity=".85"/>' +
          '<rect x="160" y="152" width="160" height="20" fill="#eab394" opacity=".85"/>') +
        '<path d="M163 95H317" stroke="#637d80" stroke-width="1"/>' +
        (tropical ? '<path d="M170 75H310M170 115H310" ' :
          '<path d="M170 38H310M170 152H310" ') +
        'stroke="#9c5d42" stroke-width="1.5" stroke-dasharray="4 4"/>' +
        '</g><text x="18" y="30" fill="#17343d" font-size="15" font-weight="700">' + title +
        '</text></svg>';
    } else if (data.figure === "date-line-role" || data.figure === "date-line-crossing") {
      var projection = global.d3.geoEquirectangular().rotate([-180, 0]).scale(69).translate([240, 116]);
      var land = global.d3.geoPath(projection)(bundle.anchors);
      var crossing = data.figure === "date-line-crossing";
      var overlay = crossing ?
        '<defs><marker id="rq-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#a84c35"/></marker></defs>' +
        '<path d="M150 82H326" stroke="#a84c35" stroke-width="3" marker-end="url(#rq-arrow)"/>' +
        '<path d="M330 157H154" stroke="#a84c35" stroke-width="3" marker-end="url(#rq-arrow)"/>' +
        '<text x="165" y="69" fill="#672d22" font-size="14" font-weight="700">Eastward</text>' +
        '<text x="320" y="179" text-anchor="end" fill="#672d22" font-size="14" font-weight="700">Westward</text>' :
        (side === "back" ? '<path d="M240 16L240 48L220 67L220 92L257 113L257 151L238 171L238 212" fill="none" stroke="#a84c35" stroke-width="3" stroke-dasharray="7 4"/>' +
          '<text x="263" y="56" fill="#672d22" font-size="13" font-weight="700">Date boundary, schematic</text>' : '');
      figure.innerHTML = '<svg viewBox="0 0 480 232" role="img" aria-label="' + title + '">' +
        '<rect width="480" height="232" fill="#b8d9df"/>' +
        '<path d="' + land + '" fill="#e9dfca" stroke="#9dad9f" stroke-width=".7"/>' +
        '<path d="M240 13V216" stroke="#245b70" stroke-width="2" stroke-dasharray="5 5"/>' +
        overlay + '<text x="12" y="24" fill="#17343d" font-size="13" font-weight="700">' +
        title + '</text><text x="246" y="224" fill="#245b70" font-size="11">180° meridian</text>' +
        '</svg>';
    } else {
      throw new Error("Unknown reference figure: " + data.figure);
    }
    host.appendChild(figure);
  }

  function mountLine(root, data, state, side, bundle) {
    var host = root.querySelector(".rq-interaction");
    var stage = element("div", "rq-globe-stage");
    var canvas = element("canvas", "rq-globe");
    canvas.setAttribute("aria-label", "Drag to rotate the globe. Tap once to place a reference line.");
    stage.appendChild(canvas);
    host.appendChild(stage);

    var ctx = canvas.getContext("2d");
    var projection = global.d3.geoOrthographic().clipAngle(90).precision(0.4);
    var path = global.d3.geoPath(projection, ctx);
    var graticule = global.d3.geoGraticule().step([30, 30])();
    var dragging = null;
    var size = 0;
    var ratio = 1;

    function paint(geometry, fill, stroke, width, dash) {
      ctx.save();
      ctx.beginPath();
      path(geometry);
      if (fill) { ctx.fillStyle = fill; ctx.fill(); }
      if (stroke) {
        ctx.strokeStyle = stroke;
        ctx.lineWidth = width || 1;
        ctx.setLineDash(dash || []);
        ctx.stroke();
      }
      ctx.restore();
    }

    function draw() {
      ctx.clearRect(0, 0, size, size);
      projection.rotate(state.rotation);
      paint(SPHERE, color(root, "--ocean", "#9bc5cf"), color(root, "--line", "#c5c5b8"), 1.3);
      paint(graticule, null, "rgba(255,255,255,.27)", .7);
      paint(bundle.anchors, color(root, "--land", "#e6d8bd"), color(root, "--line", "#c5c5b8"), .6);
      if (side === "front" && state.guess !== null && state.guess !== undefined) {
        paint(lineGeometry(data.axis, state.guess), null, color(root, "--guess", "#bd7e0f"), 3.5);
      }
      if (side === "back") {
        paint(lineGeometry(data.axis, data.target), null, color(root, "--accent", "#bd4d35"), 3);
      }
    }

    function resize() {
      size = Math.max(280, Math.round(stage.getBoundingClientRect().width));
      ratio = Math.min(global.devicePixelRatio || 1, 2);
      canvas.width = Math.round(size * ratio);
      canvas.height = Math.round(size * ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      projection.fitExtent([[12, 12], [size - 12, size - 12]], SPHERE);
      draw();
    }

    canvas.style.touchAction = "none";

    function point(event) {
      var rect = canvas.getBoundingClientRect();
      return [event.clientX - rect.left, event.clientY - rect.top];
    }

    function begin(event, id) {
      if (dragging) return; // Android sends pointerdown before touchstart.
      dragging = { id: id, start: point(event), rotation: state.rotation.slice(), moved: false };
    }
    function move(event) {
      if (!dragging) return;
      var current = point(event);
      var dx = current[0] - dragging.start[0];
      var dy = current[1] - dragging.start[1];
      if (Math.hypot(dx, dy) <= 6) return;
      dragging.moved = true;
      state.rotation = [dragging.rotation[0] + dx * .45,
        Math.max(-85, Math.min(85, dragging.rotation[1] - dy * .45)), 0];
      save(root.dataset.key, state);
      draw();
    }
    function end(event) {
      if (!dragging) return;
      if (side === "front" && !dragging.moved) {
        var current = point(event);
        var inverted = projection.invert(current);
        var center = projection.translate();
        if (inverted && Math.hypot(current[0] - center[0], current[1] - center[1]) <= projection.scale()) {
          state.guess = Math.round(inverted[data.axis === "lat" ? 1 : 0] * 2) / 2;
          save(root.dataset.key, state);
          root.querySelector(".rq-help").textContent = "Placed: " + degreeLabel(data.axis, state.guess) + ". Tap again to adjust.";
          draw();
        }
      }
      dragging = null;
    }
    canvas.addEventListener("pointerdown", function (event) {
      begin(event, event.pointerId);
      try { canvas.setPointerCapture(event.pointerId); } catch (error) { /* older WebViews */ }
      event.preventDefault();
    });
    canvas.addEventListener("pointermove", function (event) {
      if (dragging && dragging.id === event.pointerId) move(event);
    });
    canvas.addEventListener("pointerup", function (event) {
      if (dragging && dragging.id === event.pointerId) end(event);
      event.preventDefault();
    });
    // AnkiDroid can cancel the pointer stream mid-swipe while touch events continue.
    // The non-passive touch path owns the same gesture until the actual touch ends.
    canvas.addEventListener("touchstart", function (event) {
      if (event.touches.length === 1) begin(event.touches[0], "touch");
      event.preventDefault();
    }, { passive: false });
    canvas.addEventListener("touchmove", function (event) {
      if (event.touches.length === 1) move(event.touches[0]);
      event.preventDefault();
    }, { passive: false });
    canvas.addEventListener("touchend", function (event) {
      if (event.changedTouches.length) end(event.changedTouches[0]);
      event.preventDefault();
    }, { passive: false });
    resize();
    if (global.ResizeObserver) new global.ResizeObserver(resize).observe(stage);
    else global.addEventListener("resize", resize);
    if (side === "front") root.querySelector(".rq-help").textContent = "Drag to rotate. Tap the globe to place the line.";
    if (side === "back") {
      root.querySelector(".rq-result").textContent = degreeLabel(data.axis, data.target);
    }
  }

  function mountRecall(root, data, state, side) {
    var host = root.querySelector(".rq-interaction");
    if (side === "front") {
      if (data.grading !== "short") return;
      var response = element("input", "rq-response");
      response.setAttribute("aria-label", "Your answer");
      response.placeholder = "Your answer";
      response.type = "text";
      response.value = state.response || "";
      response.addEventListener("input", function () {
        state.response = response.value;
        save(root.dataset.key, state);
      });
      host.appendChild(response);
      return;
    }
    root.querySelector(".rq-result").textContent = data.answer;
  }

  function mountClock(root, data, state, side) {
    var sample = state.sample;
    if (!sample) {
      root.querySelector(".rq-result").textContent = "No saved prompt. Return to the front and try again.";
      return;
    }
    root.querySelector(".rq-prompt").textContent = "If it is " + String(sample.hour).padStart(2, "0") +
      ":00 in " + sample.from + ", what time and relative date is it in " + sample.to + "?";
    var host = root.querySelector(".rq-interaction");
    var box = element("div", "rq-clock");
    box.appendChild(element("div", "rq-clock-route", sample.from + "  →  " + sample.to));
    var answer = clockAnswer(sample);
    if (side === "front") {
      var inputs = element("div", "rq-clock-inputs");
      var hourLabel = element("label", "", "Hour (0–23)");
      var hour = element("input");
      hour.type = "number";
      hour.min = "0";
      hour.max = "23";
      hour.step = "1";
      hour.inputMode = "numeric";
      hour.value = state.hour === undefined ? "" : state.hour;
      hourLabel.appendChild(hour);
      var dayLabelNode = element("label", "", "Relative date");
      var day = element("select");
      [["", "Choose"], ["-1", "Previous day"], ["0", "Same day"], ["1", "Next day"]].forEach(function (item) {
        var option = element("option", "", item[1]);
        option.value = item[0];
        day.appendChild(option);
      });
      day.value = state.day === undefined ? "" : String(state.day);
      dayLabelNode.appendChild(day);
      function update() {
        var number = hour.value === "" ? null : Number(hour.value);
        state.hour = number !== null && Number.isInteger(number) && number >= 0 && number <= 23 ? number : undefined;
        state.day = day.value === "" ? undefined : Number(day.value);
        save(root.dataset.key, state);
      }
      hour.addEventListener("input", update);
      day.addEventListener("change", update);
      inputs.appendChild(hourLabel);
      inputs.appendChild(dayLabelNode);
      box.appendChild(inputs);
      root.querySelector(".rq-help").textContent = "Give the hour and whether the date changes.";
    } else {
      box.appendChild(element("div", "rq-clock-answer", String(answer.hour).padStart(2, "0") + ":00 · " + dayLabel(answer.day)));
    }
    host.appendChild(box);
  }

  function mount(root, bundle) {
    if (!root || root.dataset.ready === "true") return;
    root.dataset.ready = "true";
    var data = decode(root.dataset.payload);
    var side = root.dataset.side;
    var state = side === "front" ? (data.mode === "line" ?
      { rotation: [Math.random() * 360 - 180, Math.random() * 30 - 15, 0], guess: null } :
      data.mode === "clock" ? { sample: chooseClockSample() } : { response: "" }) : load(root.dataset.key) || {};
    if (side === "front") save(root.dataset.key, state);
    if (side === "back") mountFigure(root, data, side, bundle);
    if (data.mode === "line") mountLine(root, data, state, side, bundle);
    else if (data.mode === "recall") mountRecall(root, data, state, side);
    else if (data.mode === "clock") mountClock(root, data, state, side);
    else throw new Error("Unknown QA mode: " + data.mode);
  }

  global.GeoReferenceQA = { mount: mount, angleError: angleError, clockAnswer: clockAnswer, chooseClockSample: chooseClockSample };
})(window);
