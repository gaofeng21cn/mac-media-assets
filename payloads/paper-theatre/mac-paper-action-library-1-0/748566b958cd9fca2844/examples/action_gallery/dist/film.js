"use strict";
(() => {
  // src/kit/motion.ts
  var clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  var mix = (a, b, p) => a + (b - a) * p;
  var smooth = (v) => {
    const p = clamp(v);
    return p * p * (3 - 2 * p);
  };
  var easeOut = (p) => 1 - (1 - clamp(p)) ** 3;
  var progress = (t, start, end) => end === start ? Number(t >= end) : clamp((t - start) / (end - start));
  var phase = (t, start, end) => smooth(progress(t, start, end));
  var hash = (n) => {
    const v = Math.sin(n * 127.13 + 41.17) * 43758.5453;
    return v - Math.floor(v);
  };
  var ringDown = (t, contact, amplitude, decay, hz) => {
    const dt = t - contact;
    return dt < 0 ? 0 : amplitude * Math.exp(-decay * dt) * Math.sin(dt * Math.PI * 2 * hz);
  };
  function liftPose(t, start, peak, end, from, to, lift = 26) {
    const up = phase(t, start, peak), down = phase(t, peak, end), rise = up < 1 ? up : 1 - down, travel = down, fall = easeOut(travel);
    return {
      x: mix(from.x, to.x, fall),
      y: mix(from.y, to.y, fall) - rise * lift,
      rotation: mix(from.rotation || 0, to.rotation || 0, easeOut(fall)),
      scale: mix(from.scale ?? 1, to.scale ?? 1, easeOut(fall)),
      opacity: mix(from.opacity ?? 1, to.opacity ?? 1, rise),
      lift01: rise
    };
  }
  function tearPose(t, start, end, axis = "v") {
    const p = easeOut(phase(t, start, end));
    const gap = p * 46;
    return axis === "v" ? {
      amount: p,
      left: { x: -gap, y: p * 2, rotation: -p * 0.045 },
      right: { x: gap, y: -p * 1.5, rotation: p * 0.05 }
    } : {
      amount: p,
      left: { x: -p * 2, y: -gap, rotation: -p * 0.04 },
      right: { x: p * 1.5, y: gap, rotation: p * 0.045 }
    };
  }
  function pageTurn(t, start, end) {
    const p = smooth(phase(t, start, end));
    return {
      progress: p,
      corner: Math.sin(p * Math.PI),
      bend: Math.sin(p * Math.PI) * 0.34,
      flip: p < 0.5 ? -p * 2 : (p - 1) * 2
    };
  }
  function unroll(t, start, end, length) {
    const p = smooth(phase(t, start, end));
    return {
      amount: p,
      length: p * length,
      curl: (1 - p) * Math.min(1, length / 90)
    };
  }
  function wrapBand(t, start, end, turns = 1) {
    const p = smooth(phase(t, start, end));
    return { wrap01: p, turns: p * turns, tension: Math.sin(p * Math.PI) };
  }
  function cutAlong(t, start, severAt, end) {
    const progress2 = easeOut(phase(t, start, severAt)), after = smooth(phase(t, severAt, end));
    return {
      progress: progress2,
      severed: t >= severAt,
      blade: progress2,
      spread: after
    };
  }
  function strokeAlong(t, start, end, hold = 0) {
    const p = progress(t, start + hold, end), q = smooth(p);
    return {
      fraction: q,
      drawing: t >= start + hold && t < end,
      penDown: t >= start + hold,
      speed: t > start + hold && t <= end ? 6 * q * (1 - q) : 0
    };
  }
  function clipSnap(t, closeAt, openWidth = 1) {
    const close = easeOut(phase(t, closeAt - 0.28, closeAt)), recoil = t >= closeAt ? ringDown(t, closeAt, 0.22, 9, 4) : 0;
    return {
      gap: mix(openWidth, 0, close) + recoil,
      shut: t >= closeAt,
      recoil
    };
  }
  function dropSettle(t, release, impact, from, to) {
    const fall = easeOut(phase(t, release, impact)), ring = t >= impact ? ringDown(t, impact, 1, 7, 3.4) : 0;
    return {
      x: mix(from.x, to.x, fall) + ring * 2.4,
      y: mix(from.y, to.y, fall) - Math.sin(Math.PI * fall) * 42,
      rotation: ring * 0.05,
      scale: 1 - Math.abs(ring) * 0.035,
      height: Math.sin(Math.PI * clamp(fall)),
      landed: t >= impact
    };
  }
  function unfoldPanels(t, start, end, panels) {
    const total = smooth(phase(t, start, end));
    const open = Array.from(
      { length: panels },
      (_, i) => smooth(clamp((total - i * (0.55 / panels)) * (panels / 0.55)))
    );
    return { open, total };
  }

  // src/kit/stage.ts
  var Stage = class {
    constructor(g, width = 1280, height = 720) {
      this.g = g;
      this.width = width;
      this.height = height;
    }
    images = {};
    assets = {};
    extents = {};
    layoutData = { subjects: [], text: [] };
    clips = [];
    tracking = true;
    async load(list) {
      await Promise.all(
        list.map(
          (a) => new Promise((resolve, reject) => {
            const im = new Image();
            this.assets[a.asset_id] = a;
            im.onload = () => {
              this.images[a.asset_id] = im;
              const c = document.createElement("canvas");
              c.width = 180;
              c.height = Math.max(1, Math.round(180 * im.height / im.width));
              const x = c.getContext("2d", { willReadFrequently: true });
              x.drawImage(im, 0, 0, c.width, c.height);
              let ext = { x: 0, y: 0, w: 1, h: 1 };
              try {
                const data = x.getImageData(0, 0, c.width, c.height).data;
                let l = c.width, r = 0, t = c.height, b = 0;
                for (let y = 0; y < c.height; y++)
                  for (let i = 0; i < c.width; i++)
                    if (data[(y * c.width + i) * 4 + 3] > 24) {
                      l = Math.min(l, i);
                      r = Math.max(r, i + 1);
                      t = Math.min(t, y);
                      b = Math.max(b, y + 1);
                    }
                if (r > l)
                  ext = {
                    x: l / c.width,
                    y: t / c.height,
                    w: (r - l) / c.width,
                    h: (b - t) / c.height
                  };
              } catch (e) {
                if (!(e instanceof DOMException) || e.name !== "SecurityError") {
                  reject(e);
                  return;
                }
              }
              this.extents[a.asset_id] = ext;
              resolve();
            };
            im.onerror = () => reject(Error(`\u7D20\u6750\u65E0\u6CD5\u52A0\u8F7D ${a.path}`));
            im.src = a.path;
          })
        )
      );
    }
    reset() {
      this.g.setTransform(1, 0, 0, 1, 0, 0);
      this.g.globalAlpha = 1;
      this.layoutData = { subjects: [], text: [] };
      this.clips = [];
      this.tracking = true;
    }
    layout() {
      return this.layoutData;
    }
    group(pose, draw) {
      const g = this.g;
      g.save();
      try {
        g.translate(pose.x, pose.y);
        g.rotate(pose.rotation || 0);
        g.scale(pose.scale ?? 1, pose.scale ?? 1);
        g.globalAlpha *= pose.opacity ?? 1;
        draw();
      } finally {
        g.restore();
      }
    }
    camera(c, draw) {
      const g = this.g;
      g.save();
      try {
        g.translate(this.width / 2, this.height * 0.42);
        if (c.rotation) g.rotate(c.rotation);
        g.scale(c.zoom, c.zoom);
        g.translate(-c.x, -c.y);
        draw();
      } finally {
        g.restore();
      }
    }
    worldRect(rect) {
      const m = this.g.getTransform(), p = [
        [rect.x, rect.y],
        [rect.x + rect.w, rect.y],
        [rect.x, rect.y + rect.h],
        [rect.x + rect.w, rect.y + rect.h]
      ].map(([x, y]) => ({
        x: m.a * x + m.c * y + m.e,
        y: m.b * x + m.d * y + m.f
      }));
      const xs = p.map((p2) => p2.x), ys = p.map((p2) => p2.y);
      return {
        x: Math.min(...xs),
        y: Math.min(...ys),
        w: Math.max(...xs) - Math.min(...xs),
        h: Math.max(...ys) - Math.min(...ys)
      };
    }
    bounds(rect, kind = "subjects") {
      if (!this.tracking || this.g.globalAlpha < 0.025) return;
      let r = this.worldRect(rect);
      for (const c of this.clips) {
        const x = Math.max(r.x, c.x), y = Math.max(r.y, c.y);
        r = {
          x,
          y,
          w: Math.max(0, Math.min(r.x + r.w, c.x + c.w) - x),
          h: Math.max(0, Math.min(r.y + r.h, c.y + c.h) - y)
        };
      }
      if (r.w && r.h) this.layoutData[kind].push({ ...r, name: rect.name });
    }
    clip(path, rect, draw) {
      const g = this.g;
      g.save();
      path();
      g.clip();
      this.clips.push(this.worldRect(rect));
      try {
        draw();
      } finally {
        this.clips.pop();
        g.restore();
      }
    }
    shadow(lift = 2) {
      const g = this.g;
      g.shadowColor = "rgba(38,35,28,.23)";
      g.shadowBlur = 3 + lift * 0.7;
      g.shadowOffsetX = 1 + lift * 0.15;
      g.shadowOffsetY = 2 + lift * 0.5;
    }
    image(id, p) {
      const im = this.images[id];
      if (!im) throw Error(`\u672A\u767B\u8BB0\u7D20\u6750 ${id}`);
      const h = p.w * im.height / im.width, a = p.anchor || this.assets[id].registration?.pivot || { x: 0.5, y: 0.5 };
      this.group(p, () => {
        this.shadow(p.lift ?? 3);
        this.g.drawImage(im, -p.w * a.x, -h * a.y, p.w, h);
        const e = this.extents[id];
        this.bounds({
          x: p.w * (e.x - a.x),
          y: h * (e.y - a.y),
          w: p.w * e.w,
          h: h * e.h,
          name: id
        });
      });
    }
    anchor(id, w, name) {
      const a = this.assets[id].registration?.anchors?.[name];
      if (!a) throw Error(`\u7F3A\u5C11\u8FDE\u63A5\u70B9 ${id}.${name}`);
      const pivot = this.assets[id].registration?.pivot || { x: 0.5, y: 0.5 }, im = this.images[id];
      return {
        x: (a.x - pivot.x) * w,
        y: (a.y - pivot.y) * w * im.height / im.width
      };
    }
    text(text, x, y, size = 26, color = "#254a48", options = {}) {
      const g = this.g;
      g.save();
      g.shadowColor = "transparent";
      g.font = `${options.weight || 600} ${size}px "Kaiti SC","STKaiti",serif`;
      g.textAlign = options.align || "center";
      g.textBaseline = "middle";
      g.fillStyle = color;
      g.fillText(text, x, y);
      const m = g.measureText(text), w = m.width;
      this.bounds(
        {
          x: x - (g.textAlign === "center" ? w / 2 : g.textAlign === "right" ? w : 0),
          y: y - size * 0.62,
          w,
          h: size * 1.24,
          name: text
        },
        "text"
      );
      g.restore();
    }
    edge(x, y, w, h, seed = 1, rough = 4) {
      const g = this.g, n = Math.max(7, Math.round(w / 28));
      g.beginPath();
      g.moveTo(x, y);
      for (let i = 1; i <= n; i++)
        g.lineTo(x + w * i / n, y + (hash(seed + i) - 0.5) * rough);
      for (let i = 1; i <= 7; i++)
        g.lineTo(x + w + (hash(seed + 50 + i) - 0.5) * rough, y + h * i / 7);
      for (let i = n - 1; i >= 0; i--)
        g.lineTo(x + w * i / n, y + h + (hash(seed + 100 + i) - 0.5) * rough);
      for (let i = 6; i >= 1; i--)
        g.lineTo(x + (hash(seed + 150 + i) - 0.5) * rough, y + h * i / 7);
      g.closePath();
    }
    paper(p) {
      this.group(p, () => {
        const g = this.g, seed = p.seed || 1;
        this.shadow(p.lift ?? 2);
        this.edge(-p.w / 2, -p.h / 2, p.w, p.h, seed);
        g.fillStyle = p.color || "#f4ead7";
        g.fill();
        g.shadowColor = "transparent";
        g.strokeStyle = "#fff9eb99";
        g.lineWidth = 1.3;
        g.stroke();
        this.bounds({
          x: -p.w / 2,
          y: -p.h / 2,
          w: p.w,
          h: p.h,
          name: p.name || "paper"
        });
        this.clip(
          () => this.edge(-p.w / 2, -p.h / 2, p.w, p.h, seed),
          { x: -p.w / 2, y: -p.h / 2, w: p.w, h: p.h },
          () => {
            g.globalAlpha *= 0.09;
            for (let i = 0; i < p.w * p.h / 190; i++) {
              g.fillStyle = i % 3 ? "#816e52" : "#fffdf5";
              g.fillRect(
                (hash(seed + i * 3) - 0.5) * p.w,
                (hash(seed + i * 7) - 0.5) * p.h,
                0.7 + hash(i) * 2,
                0.5
              );
            }
          }
        );
      });
    }
    background() {
      const g = this.g;
      g.fillStyle = "#e9e4d8";
      g.fillRect(0, 0, this.width, this.height);
      g.save();
      for (let i = 0; i < 2200; i++) {
        g.globalAlpha = 0.025 + hash(i) * 0.04;
        g.fillStyle = i % 4 ? "#79745f" : "#ffffff";
        g.fillRect(
          hash(i + 8) * this.width,
          hash(i + 14) * this.height,
          0.6 + hash(i + 9) * 3,
          0.8
        );
      }
      g.restore();
    }
  };

  // src/kit/overlays.ts
  function brandMark(s, brand) {
    s.group({ x: 69, y: 44, rotation: -0.035 }, () => {
      s.paper({
        x: 0,
        y: 0,
        w: 97,
        h: 40,
        color: brand.paper,
        seed: 99,
        name: "brand"
      });
      s.text(brand.text, 0, -1, 21, brand.ink);
      const g = s.g;
      g.strokeStyle = brand.accent;
      g.lineWidth = 2;
      g.beginPath();
      g.moveTo(-29, 13);
      g.lineTo(25, 12);
      g.stroke();
    });
  }
  function caption(s, score2, t) {
    const c = score2.cues.find((c2) => t >= c2.start && t < c2.end);
    if (!c) return;
    const g = s.g;
    g.save();
    g.font = '500 27px "PingFang SC",sans-serif';
    g.textAlign = "center";
    g.textBaseline = "middle";
    let luminance = 200;
    try {
      const samples = [0.25, 0.375, 0.5, 0.625, 0.75].map((x) => {
        const d = g.getImageData(Math.round(s.width * x), s.height - 67, 1, 1).data;
        return d[0] * 0.2126 + d[1] * 0.7152 + d[2] * 0.0722;
      });
      luminance = samples.reduce((a, b) => a + b, 0) / samples.length;
    } catch {
    }
    const dark = luminance < 142;
    g.shadowColor = "transparent";
    g.lineJoin = "round";
    g.lineWidth = dark ? 3.6 : 2.3;
    g.strokeStyle = dark ? "#263733" : "rgba(255,249,234,.78)";
    g.strokeText(c.text, s.width / 2, s.height - 67);
    g.fillStyle = dark ? "#fff8e8" : "#253f3b";
    g.fillText(c.text, s.width / 2, s.height - 67);
    const m = g.measureText(c.text);
    const rect = {
      x: s.width / 2 - m.width / 2,
      y: s.height - 84,
      w: m.width,
      h: 34,
      name: c.text
    };
    g.restore();
    return rect;
  }

  // src/kit/player.ts
  function mount(config) {
    const canvas = document.querySelector("#film"), s = new Stage(canvas.getContext("2d"), canvas.width, canvas.height), score2 = config.score;
    const clean = new URLSearchParams(location.search).has("clean");
    const controls = document.querySelector("nav"), audio = document.querySelector("#voice"), play = document.querySelector("#play"), seek = document.querySelector("#seek");
    const chooser = document.createElement("select");
    chooser.setAttribute("aria-label", "\u9009\u62E9\u955C\u5934");
    chooser.innerHTML = '<option value="all">\u6574\u7247</option>' + score2.shots.map((b) => `<option value="${b.id}">${b.title}</option>`).join("");
    controls.append(chooser);
    const initialShot = new URLSearchParams(location.search).get("shot");
    if (score2.shots.some((b) => b.id === initialShot)) chooser.value = initialShot;
    const speed = document.createElement("select");
    speed.setAttribute("aria-label", "\u64AD\u653E\u901F\u5EA6");
    speed.innerHTML = '<option value="1">\u6B63\u5E38\u901F\u5EA6</option><option value="0.5">\u534A\u901F\u5BA1\u7247</option>';
    controls.append(speed);
    const loop = document.createElement("input");
    loop.type = "checkbox";
    loop.id = "loop";
    const loopLabel = document.createElement("label");
    loopLabel.append(loop, document.createTextNode("\u5FAA\u73AF"));
    controls.append(loopLabel);
    const cleanLink = document.createElement("a");
    cleanLink.href = clean ? "index.html" : "index.html?clean=1";
    cleanLink.textContent = clean ? "\u663E\u793A\u5B57\u5E55" : "\u53BB\u6587\u5B57\u5BA1\u7247";
    controls.append(cleanLink);
    const clock = document.createElement("output");
    controls.append(clock);
    let current = 0, running = false, previous = 0;
    const range = () => {
      const b = score2.shots.find((b2) => b2.id === chooser.value);
      return b ? [b.start, b.end] : [0, score2.duration];
    };
    function draw(time) {
      current = clamp(time, 0, score2.duration - 1e-6);
      const i = Math.max(
        0,
        score2.shots.findIndex((b) => current >= b.start && current < b.end)
      );
      const beat = score2.shots[i], shot = config.shots.find((s2) => s2.id === beat.id);
      if (!shot) throw Error(`\u7F3A\u5C11\u955C\u5934 ${beat.id}`);
      s.reset();
      s.background();
      const ctx = {
        stage: s,
        t: current - beat.start,
        globalTime: current,
        beat,
        clean
      };
      const camera = shot.camera?.(ctx) || {
        x: s.width / 2,
        y: s.height * 0.42,
        zoom: 1
      };
      s.camera(camera, () => shot.render(ctx));
      s.tracking = false;
      if (config.brand) brandMark(s, config.brand);
      const subtitle = !clean ? caption(s, score2, current) : void 0;
      s.tracking = true;
      window.__layout = {
        ...s.layout(),
        subtitle
      };
      window.__state = {
        scene: i + 1,
        time: current,
        localTime: ctx.t,
        shot: beat.id,
        progress: ctx.t / (beat.end - beat.start),
        events: beat.events
      };
      window.__styleId = beat.styleId || score2.style?.appliedStyleId;
      seek.value = String(current / score2.duration);
      clock.textContent = `${current.toFixed(2)} / ${score2.duration.toFixed(2)} \u79D2`;
    }
    window.__seek = draw;
    window.__cuts = [...score2.shots.map((s2) => s2.start), score2.duration];
    window.__total = score2.duration;
    window.__score = score2;
    window.__kitVersion = "1.2.0";
    window.__rendererId = "canvas2d";
    window.__requestedStyleId = score2.style?.styleId;
    window.__styleId = score2.style?.appliedStyleId;
    controls.inert = true;
    const ready = window.__ready = s.load(config.assets).then(async () => {
      await document.fonts.ready;
      draw(range()[0]);
      controls.inert = false;
    });
    const pause = () => {
      running = false;
      audio?.pause();
      play.textContent = "\u64AD\u653E";
    };
    play.onclick = async () => {
      await ready;
      if (running) {
        pause();
        return;
      }
      const [start, end] = range();
      if (current < start || current >= end - 1 / score2.fps) draw(start);
      if (audio) {
        audio.currentTime = current;
        audio.playbackRate = Number(speed.value);
        await audio.play();
      }
      running = true;
      previous = performance.now();
      play.textContent = "\u6682\u505C";
    };
    seek.oninput = () => {
      draw(Number(seek.value) * score2.duration);
      if (audio) audio.currentTime = current;
    };
    chooser.onchange = () => {
      pause();
      draw(range()[0]);
      if (audio) audio.currentTime = current;
    };
    speed.onchange = () => {
      if (audio) audio.playbackRate = Number(speed.value);
    };
    for (const [name, delta] of [
      ["\u4E0A\u4E00\u5E27", -1],
      ["\u4E0B\u4E00\u5E27", 1]
    ]) {
      const b = document.createElement("button");
      b.textContent = name;
      b.onclick = () => {
        pause();
        draw(current + delta / score2.fps);
        if (audio) audio.currentTime = current;
      };
      controls.append(b);
    }
    if (audio)
      audio.onended = () => {
        if (!loop.checked) pause();
      };
    function tick(now) {
      if (running) {
        const [start, end] = range();
        let next = audio ? audio.currentTime : current + (now - previous) / 1e3 * Number(speed.value);
        if (next >= end - 1 / score2.fps) {
          if (loop.checked) {
            next = start;
            if (audio) {
              audio.currentTime = start;
              void audio.play();
            }
          } else {
            next = end - 1 / score2.fps;
            pause();
          }
        }
        draw(next);
      }
      previous = now;
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
    return { stage: s, ready, draw };
  }

  // src/kit/paths.ts
  function measurePath(commands, samples = 48) {
    let p = { x: 0, y: 0 }, length = 0, lifted = true;
    const segments = [];
    const origin = commands.length ? { x: commands[0].x, y: commands[0].y } : p;
    const append = (b) => {
      const d = Math.hypot(b.x - p.x, b.y - p.y);
      if (d > 1e-9) {
        segments.push({ a: p, b, start: length, length: d, move: lifted });
        length += d;
        lifted = false;
      }
      p = b;
    };
    for (const c of commands) {
      if (c.op === "M") {
        p = { x: c.x, y: c.y };
        lifted = true;
      } else if (c.op === "L") append({ x: c.x, y: c.y });
      else {
        const a = p;
        for (let i = 1; i <= Math.max(2, samples); i++) {
          const t = i / Math.max(2, samples), u = 1 - t;
          const coordinate = (axis) => c.op === "Q" ? u * u * a[axis] + 2 * u * t * (axis === "x" ? c.cx : c.cy) + t * t * c[axis] : u * u * u * a[axis] + 3 * u * u * t * (axis === "x" ? c.c1x : c.c1y) + 3 * u * t * t * (axis === "x" ? c.c2x : c.c2y) + t * t * t * c[axis];
          append({ x: coordinate("x"), y: coordinate("y") });
        }
      }
    }
    return { segments, length, origin };
  }

  // src/kit/materials.ts
  function grain(g, w, h, seed = 1, amount = 0.08, density = 450) {
    g.save();
    for (let i = 0; i < density; i++) {
      g.fillStyle = i % 3 ? `rgba(73,61,43,${amount})` : `rgba(255,255,244,${amount})`;
      const x = (hash(seed + i * 7) - 0.5) * w, y = (hash(seed + i * 11) - 0.5) * h;
      g.fillRect(x, y, 0.6 + hash(i) * 2.2, 0.5 + hash(i + 33) * 0.8);
    }
    g.restore();
  }
  function tape(s, pose, w = 58, seed = 1) {
    s.group(pose, () => {
      const g = s.g;
      s.shadow(0.4);
      s.edge(-w / 2, -10, w, 20, seed, 3.5);
      g.fillStyle = "rgba(237,201,129,.62)";
      g.fill();
      g.shadowColor = "transparent";
      g.strokeStyle = "rgba(255,252,231,.4)";
      g.lineWidth = 0.7;
      g.stroke();
      grain(g, w, 18, seed, 0.1, 50);
    });
  }

  // src/kit/actions.ts
  function liftCorner(stage, t, opts) {
    const p = liftPose(t, opts.start, opts.peak, opts.end, opts.from, opts.to, opts.lift ?? 26);
    stage.group(p, () => {
      stage.paper({
        x: 0,
        y: 0,
        w: opts.w,
        h: opts.h,
        color: opts.color,
        seed: opts.seed ?? 31,
        lift: p.lift01 * (opts.lift ?? 8) + 1,
        name: "lifted-piece"
      });
    });
    return p;
  }
  function tearSheet(stage, t, opts) {
    const axis = opts.axis ?? "v", p = tearPose(t, opts.start, opts.end, axis);
    stage.group({ x: opts.x ?? 0, y: opts.y ?? 0 }, () => {
      stage.group({ ...p.left }, () => {
        stage.paper({ x: -opts.w / 4, y: 0, w: opts.w / 2, h: opts.h, color: opts.color, seed: opts.seed ?? 41, lift: 2 + p.amount * 4, name: "tear-left" });
        opts.drawLeft?.(stage);
      });
      stage.group({ ...p.right }, () => {
        stage.paper({ x: opts.w / 4, y: 0, w: opts.w / 2, h: opts.h, color: opts.color, seed: (opts.seed ?? 41) + 1, lift: 2 + p.amount * 4, name: "tear-right" });
        opts.drawRight?.(stage);
      });
      if (p.amount > 0 && p.amount < 1) {
        const g = stage.g;
        stage.group({ x: 0, y: 0 }, () => {
          g.save();
          g.globalAlpha *= 0.5 * Math.sin(p.amount * Math.PI);
          g.strokeStyle = "#8d7c62";
          g.lineWidth = 1;
          const n = axis === "v" ? 14 : 18;
          for (let i = 0; i < n; i++) {
            const f = (i / (n - 1) - 0.5) * (axis === "v" ? opts.h : opts.w);
            const j = i * 37 % 7 - 3;
            g.beginPath();
            if (axis === "v") {
              g.moveTo(j * p.amount * 2, f);
              g.lineTo(j * p.amount * 2 + 3, f + 2);
            } else {
              g.moveTo(f, j * p.amount * 2);
              g.lineTo(f + 2, j * p.amount * 2 + 3);
            }
            g.stroke();
          }
          g.restore();
        });
      }
    });
    return p;
  }
  function turnPage(stage, t, opts) {
    const p = pageTurn(t, opts.start, opts.end);
    stage.group({ x: opts.x, y: opts.y }, () => {
      stage.paper({ x: opts.w / 4, y: 0, w: opts.w / 2, h: opts.h, color: "#f3ecdb", seed: (opts.seed ?? 61) + 2, name: "page-under" });
      const g = stage.g;
      stage.group({ x: -opts.w / 4, y: 0 }, () => {
        stage.group({ x: opts.w / 4, y: 0, scale: Math.max(0.02, Math.cos(p.flip * Math.PI * 0.5)) }, () => {
          stage.paper({ x: opts.w / 4, y: 0, w: opts.w / 2, h: opts.h, color: opts.color, seed: opts.seed ?? 61, lift: 2 + p.corner * 9, name: "page-turn" });
          opts.face?.(stage);
        });
        if (p.corner > 0.05) {
          g.save();
          const grad = g.createLinearGradient(0, -opts.h / 2, opts.w / 2, opts.h / 2);
          grad.addColorStop(0, `rgba(58,48,37,${0.34 * p.corner})`);
          grad.addColorStop(0.55, `rgba(58,48,37,${0.12 * p.corner})`);
          grad.addColorStop(1, "rgba(58,48,37,0)");
          g.globalAlpha = 1;
          g.fillStyle = grad;
          g.beginPath();
          g.moveTo(0, -opts.h / 2);
          g.quadraticCurveTo(opts.w * 0.28, 0, opts.w / 2, opts.h * 0.1);
          g.lineTo(0, opts.h / 2);
          g.closePath();
          g.fill();
          g.restore();
        }
      });
    });
    return p;
  }
  function unrollTape(stage, t, opts) {
    const p = unroll(t, opts.start, opts.end, opts.length), h = opts.h ?? 22;
    stage.group({ x: opts.x, y: opts.y }, () => {
      if (p.length > 1) {
        stage.paper({ x: p.length / 2, y: 0, w: p.length, h, color: opts.color ?? "#e7dcc0", seed: opts.seed ?? 81, lift: 2, name: "tape" });
        opts.ticks?.(stage, p.length);
      }
      stage.group({ x: 0, y: 0 }, () => {
        stage.group({ x: 0, y: 0, scale: 1 - p.curl * 0.4 }, () => {
          stage.paper({ x: 0, y: 0, w: 34, h: h + 10, color: opts.color ?? "#d9caa8", seed: (opts.seed ?? 81) + 3, lift: 4, name: "tape-roll" });
        });
      });
    });
    return p;
  }
  function wrapAround(stage, t, opts) {
    const p = wrapBand(t, opts.start, opts.end, opts.turns ?? 1);
    stage.group({ x: opts.x, y: opts.y }, () => {
      opts.drawSubject?.();
      if (p.wrap01 > 0.01) {
        const g = stage.g, steps = Math.max(2, Math.round(p.turns * 8));
        g.save();
        g.globalAlpha *= 0.94;
        g.strokeStyle = opts.color ?? "#d9c8a4";
        g.lineWidth = Math.max(4, opts.ry * 0.16);
        g.lineCap = "round";
        for (let i = 0; i < steps; i++) {
          const f = (i + 1) / steps, y = (f - 0.5) * opts.ry * 2;
          const k = Math.sqrt(Math.max(0, 1 - (y / opts.ry) ** 2)), wob = Math.sin(p.tension * Math.PI) * 3;
          g.beginPath();
          g.moveTo(-opts.rx * k + wob, y);
          g.quadraticCurveTo(0, y + opts.ry * 0.12, opts.rx * k - wob, y);
          g.stroke();
        }
        g.restore();
      }
    });
    return p;
  }
  function cutOpen(stage, t, opts) {
    const p = cutAlong(t, opts.start, opts.severAt, opts.end), vertical = (opts.axis ?? "v") === "v";
    stage.group({ x: opts.x, y: opts.y }, () => {
      const g = stage.g;
      const top = { x: 0, y: -opts.h * p.spread * 0.28, rotation: -p.spread * 0.03 }, bottom = { x: 0, y: opts.h * p.spread * 0.28, rotation: p.spread * 0.035 };
      stage.group(bottom, () => opts.drawBottom?.(stage, p.spread));
      stage.group(top, () => opts.drawTop?.(stage, p.spread));
      g.save();
      g.globalAlpha *= p.severed ? 0.5 : 0.9 * p.blade;
      g.strokeStyle = p.severed ? "#6f6047" : "#fdf6e6";
      g.lineWidth = 2;
      g.beginPath();
      if (vertical) {
        g.moveTo(0, -opts.h / 2);
        g.lineTo(0, -opts.h / 2 + opts.h * p.progress);
      } else {
        g.moveTo(-opts.w / 2, 0);
        g.lineTo(-opts.w / 2 + opts.w * p.progress, 0);
      }
      g.stroke();
      g.restore();
    });
    return p;
  }
  function penStroke(stage, t, opts) {
    const p = strokeAlong(t, opts.start, opts.end, opts.hold ?? 0);
    const g = stage.g;
    g.save();
    g.strokeStyle = opts.color ?? "#3d4a48";
    g.lineWidth = opts.width ?? 2.4;
    g.lineCap = "round";
    g.lineJoin = "round";
    const d = p.fraction * opts.path.length;
    g.beginPath();
    for (const s of opts.path.segments) {
      if (s.start >= d) break;
      if (s.move) g.moveTo(s.a.x, s.a.y);
      const q = Math.min(1, (d - s.start) / s.length);
      g.lineTo(s.a.x + (s.b.x - s.a.x) * q, s.a.y + (s.b.y - s.a.y) * q);
      if (q < 1) break;
    }
    g.stroke();
    if (p.drawing) {
      g.fillStyle = opts.color ?? "#3d4a48";
      g.beginPath();
      g.arc(opts.path.segments.at(-1)?.b.x ?? 0, opts.path.segments.at(-1)?.b.y ?? 0, opts.width ?? 2.4, 0, Math.PI * 2);
      g.fill();
    }
    g.restore();
    return p;
  }
  function snapClip(stage, t, opts) {
    const p = clipSnap(t, opts.closeAt, 1);
    stage.group({ x: opts.x, y: opts.y, rotation: opts.angle ?? -0.1, scale: opts.scale ?? 1 }, () => {
      const g = stage.g;
      g.save();
      g.strokeStyle = opts.color ?? "#8c8069";
      g.lineWidth = 3;
      g.beginPath();
      g.moveTo(-6, 15);
      g.lineTo(-6, -10);
      g.bezierCurveTo(-6, -22, 10, -22, 10, -10);
      g.lineTo(10, 15);
      g.bezierCurveTo(10, 24, -12, 24, -12, 12);
      g.lineTo(-12, -8);
      g.stroke();
      g.lineWidth = 2.2;
      g.beginPath();
      g.moveTo(-6, 4 - p.gap * 5);
      g.lineTo(10, 4 - p.gap * 5);
      g.stroke();
      g.restore();
    });
    return p;
  }
  function dropSheet(stage, t, opts) {
    const p = dropSettle(t, opts.release, opts.impact, opts.from, opts.to);
    stage.group(p, () => {
      stage.paper({ x: 0, y: 0, w: opts.w, h: opts.h, color: opts.color, seed: opts.seed ?? 91, lift: 1 + p.height * 14, name: "dropped-sheet" });
      opts.face?.();
    });
    return p;
  }
  function unfoldMap(stage, t, opts) {
    const p = unfoldPanels(t, opts.start, opts.end, opts.panels), leaf = opts.w / opts.panels;
    stage.group({ x: opts.x, y: opts.y }, () => {
      for (let i = 0; i < opts.panels; i++) {
        const open = p.open[i], cx = -opts.w / 2 + leaf * (i + 0.5);
        stage.group({ x: cx, y: 0 }, () => {
          stage.group({ x: 0, y: 0, scale: Math.max(0.04, Math.sin(open * Math.PI * 0.5)) }, () => {
            stage.paper({ x: 0, y: 0, w: leaf, h: opts.h, color: opts.color, seed: (opts.seed ?? 101) + i, lift: 1 + open * 5, name: `map-leaf-${i}` });
            opts.label?.(stage, i, open);
          });
        });
      }
    });
    return p;
  }

  // examples/action_gallery/score.json
  var score_default = {
    fps: 24,
    duration: 60,
    cues: [],
    sounds: [],
    shots: [
      { id: "tear", title: "\u6495\u5F00\u63ED\u793A", start: 0, end: 6, events: { start: 0.6, done: 3.2 } },
      { id: "lift", title: "\u63ED\u8D77\u4E0E\u843D\u5B9A", start: 6, end: 12, events: { start: 0.6, peak: 2, end_ev: 4.6 } },
      { id: "page", title: "\u7FFB\u9875", start: 12, end: 18, events: { start: 0.6, end_ev: 4.2 } },
      { id: "cut", title: "\u526A\u5F00", start: 18, end: 24, events: { start: 0.5, sever: 2.6, done: 5 } },
      { id: "tape", title: "\u62C9\u51FA\u4E0E\u5C55\u5F00", start: 24, end: 30, events: { start: 0.6, done: 4.4 } },
      { id: "wrap", title: "\u7F20\u7ED5\u6536\u7D27", start: 30, end: 36, events: { start: 0.6, done: 4.6 } },
      { id: "clip", title: "\u5939\u5408", start: 36, end: 42, events: { close: 2.4, end_ev: 5 } },
      { id: "drop", title: "\u843D\u7EB8", start: 42, end: 48, events: { release: 0.5, impact: 2.6, end_ev: 5.2 } },
      { id: "map", title: "\u6298\u53E0\u56FE\u5C55\u5F00", start: 48, end: 54, events: { start: 0.6, done: 4.6 } },
      { id: "pen", title: "\u7B14\u8FF9\u7ED8\u5236", start: 54, end: 60, events: { start: 0.5, done: 4.8 } }
    ]
  };

  // examples/action_gallery/main.ts
  var score = score_default;
  var stage0 = (s, label) => {
    const g = s.g;
    s.paper({ x: 640, y: 300, w: 1360, h: 760, color: "#c9d4cb", seed: 3, lift: 0, name: "ground" });
    s.paper({ x: 640, y: 588, w: 1240, h: 260, color: "#dccdb0", seed: 5, lift: 2, name: "desk" });
    s.group({ x: 1188, y: 560, rotation: 0.05 }, () => tape(s, { x: 0, y: 0 }, 60, 11));
    s.text(label, 640, 640, 26, "#3f4d47");
  };
  var push = (from, to, p) => ({
    x: from.x + (to.x - from.x) * p,
    y: from.y + (to.y - from.y) * p,
    zoom: from.zoom + (to.zoom - from.zoom) * p
  });
  var shots = [
    {
      id: "tear",
      camera: ({ t }) => ({ x: 640, y: 340, zoom: 1 + Math.min(0.06, t * 0.012) }),
      render({ stage: s, t, beat }) {
        stage0(s, "\u6495\u5F00\uFF1A\u540C\u4E00\u5F20\u7EB8\u5206\u6210\u4E24\u534A\uFF0C\u7EA4\u7EF4\u6CBF\u7F1D\u53EF\u89C1");
        tearSheet(s, t, {
          start: beat.events.start,
          end: beat.events.done,
          x: 640,
          y: 360,
          w: 520,
          h: 320,
          color: "#f2e7cf",
          drawLeft: (st) => {
            st.text("\u5DF2\u786E\u8BA4", -130, 0, 34, "#6b5f49");
          },
          drawRight: (st) => {
            st.text("\u5F85\u8865", 130, 0, 34, "#a3604c");
          }
        });
      }
    },
    {
      id: "lift",
      camera: ({ t }) => ({ x: 640, y: 330, zoom: 1.05 - Math.min(0.05, t * 0.011) }),
      render({ stage: s, t, beat }) {
        stage0(s, "\u63ED\u8D77\uFF1A\u79BB\u5F00\u7EB8\u9762\u3001\u8D8A\u8FC7\u9AD8\u5EA6\u3001\u843D\u5230\u65B0\u4F4D\u7F6E");
        s.paper({ x: 380, y: 400, w: 300, h: 210, color: "#e6dcc2", seed: 12, name: "source" });
        s.text("\u6765\u6E90\u5C42", 380, 400, 26, "#6b5f49");
        liftCorner(s, t, {
          start: beat.events.start,
          peak: beat.events.peak,
          end: beat.events.end_ev,
          from: { x: 620, y: 400, rotation: -0.03 },
          to: { x: 900, y: 372, rotation: 0.05 },
          w: 250,
          h: 170,
          color: "#cfe0d4",
          lift: 40
        });
      }
    },
    {
      id: "page",
      camera: ({ t }) => ({ x: 640, y: 340, zoom: 1 + Math.min(0.07, t * 0.014) }),
      render({ stage: s, t, beat }) {
        stage0(s, "\u7FFB\u9875\uFF1A\u6298\u8F74\u62AC\u8D77\u3001\u7EB8\u9762\u5F2F\u6298\u3001\u5F71\u5B50\u968F\u9AD8\u5EA6\u79FB\u52A8");
        turnPage(s, t, {
          start: beat.events.start,
          end: beat.events.end_ev,
          x: 640,
          y: 360,
          w: 480,
          h: 330,
          color: "#f6efdc",
          face: (st) => {
            st.text("\u7B2C 2 \u9875", 60, -30, 30, "#5c6a60");
          }
        });
      }
    },
    {
      id: "cut",
      camera: ({ t }) => push({ x: 640, y: 350, zoom: 1.02 }, { x: 640, y: 330, zoom: 1.12 }, Math.min(1, t / 4)),
      render({ stage: s, t, beat }) {
        stage0(s, "\u526A\u5F00\uFF1A\u5200\u8DEF\u5148\u8D70\uFF0C\u526A\u65AD\u540E\u624D\u5206\u79BB");
        cutOpen(s, t, {
          start: beat.events.start,
          severAt: beat.events.sever,
          end: beat.events.done,
          x: 640,
          y: 360,
          w: 300,
          h: 300,
          drawTop: (st) => st.paper({ x: 0, y: 0, w: 300, h: 300, color: "#e9dcc0", seed: 21, lift: 3 }),
          drawBottom: (st) => st.paper({ x: 0, y: 0, w: 300, h: 300, color: "#e9dcc0", seed: 22, lift: 1 })
        });
      }
    },
    {
      id: "tape",
      camera: ({ t }) => ({ x: 640, y: 340, zoom: 1.04 }),
      render({ stage: s, t, beat }) {
        stage0(s, "\u62C9\u51FA\uFF1A\u5377\u5C3A\u5C55\u5F00\u3001\u523B\u5EA6\u6309\u540C\u4E00\u8FDB\u5EA6\u751F\u957F");
        unrollTape(s, t, {
          start: beat.events.start,
          end: beat.events.done,
          x: 330,
          y: 430,
          length: 640,
          ticks: (st, len) => {
            const g = st.g;
            g.save();
            g.strokeStyle = "#8d7f61";
            g.lineWidth = 1.4;
            for (let i = 1; i * 60 < len; i++) {
              g.beginPath();
              g.moveTo(i * 60, -6);
              g.lineTo(i * 60, 6);
              g.stroke();
            }
            g.restore();
          }
        });
      }
    },
    {
      id: "wrap",
      camera: ({ t }) => ({ x: 640, y: 350, zoom: 1.08 }),
      render({ stage: s, t, beat }) {
        stage0(s, "\u7F20\u7ED5\uFF1A\u7EF7\u5E26\u7ED5\u4E3B\u4F53\u6536\u7D27\uFF0C\u63A5\u89E6\u70B9\u771F\u5B9E\u5B58\u5728");
        s.group({ x: 640, y: 350 }, () => {
          s.paper({ x: 0, y: 0, w: 320, h: 210, color: "#d9c9a8", seed: 31, lift: 2, name: "subject" });
          s.text("\u5305\u624E\u533A", 0, 0, 30, "#5f5340");
        });
        wrapAround(s, t, {
          start: beat.events.start,
          end: beat.events.done,
          x: 640,
          y: 350,
          rx: 170,
          ry: 110,
          turns: 2
        });
      }
    },
    {
      id: "clip",
      camera: ({ t }) => ({ x: 640, y: 350, zoom: 1.16 - Math.min(0.06, t * 0.012) }),
      render({ stage: s, t, beat }) {
        stage0(s, "\u5939\u5408\uFF1A\u5939\u53E3\u5408\u62E2\u5E76\u56DE\u5F39\uFF0C\u4E0D\u662F\u6DE1\u51FA");
        s.paper({ x: 640, y: 400, w: 420, h: 240, color: "#f4ecd8", seed: 41, lift: 2 });
        s.text("\u5F85\u56FA\u5B9A", 640, 400, 30, "#5f5340");
        snapClip(s, t, { closeAt: beat.events.close, x: 640, y: 268, scale: 1.5, angle: 0.03 });
      }
    },
    {
      id: "drop",
      camera: ({ t }) => ({ x: 640, y: 340, zoom: 1.03 }),
      render({ stage: s, t, beat }) {
        stage0(s, "\u843D\u7EB8\uFF1A\u81EA\u7531\u843D\u4F53\u3001\u89E6\u9762\u3001\u56DE\u5F39\u8870\u51CF\u5230\u9759\u6B62");
        dropSheet(s, t, {
          release: beat.events.release,
          impact: beat.events.impact,
          from: { x: 300, y: 120, rotation: -0.2 },
          to: { x: 640, y: 420, rotation: 0.04 },
          w: 260,
          h: 180,
          color: "#dfe7d3",
          face: () => void 0
        });
      }
    },
    {
      id: "map",
      camera: ({ t }) => ({ x: 640, y: 350, zoom: 1.02 + Math.min(0.05, t * 0.01) }),
      render({ stage: s, t, beat }) {
        stage0(s, "\u6298\u53E0\u56FE\uFF1A\u591A\u53F6\u6309\u987A\u5E8F\u5C55\u5F00\uFF0C\u4E0D\u662F\u6574\u4F53\u7F29\u653E");
        unfoldMap(s, t, {
          start: beat.events.start,
          end: beat.events.done,
          x: 640,
          y: 370,
          w: 720,
          h: 260,
          panels: 4,
          color: "#eee3c6",
          label: (st, i, open) => {
            if (open > 0.55) st.text(`\u6B65\u9AA4 ${i + 1}`, 0, -10, 24, "#5d6a5f");
          }
        });
      }
    },
    {
      id: "pen",
      camera: ({ t }) => ({ x: 640, y: 350, zoom: 1.1 }),
      render({ stage: s, t, beat }) {
        stage0(s, "\u7B14\u8FF9\uFF1A\u62AC\u7B14\u4FDD\u7559\uFF0C\u7B14\u5C16\u8DDF\u968F\u4E66\u5199\u524D\u6CBF");
        const path = measurePath([
          { op: "M", x: 420, y: 470 },
          { op: "L", x: 620, y: 330 },
          { op: "M", x: 640, y: 330 },
          { op: "C", c1x: 760, c1y: 300, c2x: 840, c2y: 380, x: 880, y: 300 }
        ]);
        penStroke(s, t, { start: beat.events.start, end: beat.events.done, path, color: "#3f514c", width: 4 });
      }
    }
  ];
  mount({ assets: [], score, shots });
})();
//# sourceMappingURL=film.js.map
