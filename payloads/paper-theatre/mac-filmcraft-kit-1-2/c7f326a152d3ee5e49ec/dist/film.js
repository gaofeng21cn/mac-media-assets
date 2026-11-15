"use strict";
(() => {
  // src/kit/motion.ts
  var clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  var mix = (a, b, p) => a + (b - a) * p;
  var smooth = (v) => {
    const p = clamp(v);
    return p * p * (3 - 2 * p);
  };
  var progress = (t, start, end) => end === start ? Number(t >= end) : clamp((t - start) / (end - start));
  var phase = (t, start, end) => smooth(progress(t, start, end));
  var hash = (n) => {
    const v = Math.sin(n * 127.13 + 41.17) * 43758.5453;
    return v - Math.floor(v);
  };
  function arc(from, to, p, lift = 30) {
    return {
      x: mix(from.x, to.x, p),
      y: mix(from.y, to.y, p) - Math.sin(Math.PI * p) * lift
    };
  }
  var onTwos = (t, fps = 24) => Math.floor(t * fps / 2) * 2 / fps;

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
    edge(x, y, w, h, seed2 = 1, rough = 4) {
      const g = this.g, n = Math.max(7, Math.round(w / 28));
      g.beginPath();
      g.moveTo(x, y);
      for (let i = 1; i <= n; i++)
        g.lineTo(x + w * i / n, y + (hash(seed2 + i) - 0.5) * rough);
      for (let i = 1; i <= 7; i++)
        g.lineTo(x + w + (hash(seed2 + 50 + i) - 0.5) * rough, y + h * i / 7);
      for (let i = n - 1; i >= 0; i--)
        g.lineTo(x + w * i / n, y + h + (hash(seed2 + 100 + i) - 0.5) * rough);
      for (let i = 6; i >= 1; i--)
        g.lineTo(x + (hash(seed2 + 150 + i) - 0.5) * rough, y + h * i / 7);
      g.closePath();
    }
    paper(p) {
      this.group(p, () => {
        const g = this.g, seed2 = p.seed || 1;
        this.shadow(p.lift ?? 2);
        this.edge(-p.w / 2, -p.h / 2, p.w, p.h, seed2);
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
          () => this.edge(-p.w / 2, -p.h / 2, p.w, p.h, seed2),
          { x: -p.w / 2, y: -p.h / 2, w: p.w, h: p.h },
          () => {
            g.globalAlpha *= 0.09;
            for (let i = 0; i < p.w * p.h / 190; i++) {
              g.fillStyle = i % 3 ? "#816e52" : "#fffdf5";
              g.fillRect(
                (hash(seed2 + i * 3) - 0.5) * p.w,
                (hash(seed2 + i * 7) - 0.5) * p.h,
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
    g.fillStyle = "#253f3b";
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

  // src/kit/tracks.ts
  function track(keys) {
    if (!keys.length) throw Error("\u8F68\u9053\u9700\u8981\u81F3\u5C11\u4E00\u4E2A\u5173\u952E\u5E27");
    const list = [...keys].sort((a, b) => a.time - b.time);
    return (t) => {
      if (t < list[0].time) return { ...list[0].value };
      let i = 0;
      while (i + 1 < list.length && t >= list[i + 1].time) i++;
      if (i === list.length - 1) return { ...list[i].value };
      const a = list[i], b = list[i + 1];
      const p = clamp((t - a.time) / (b.time - a.time));
      const q = a.ease === "hold" ? 0 : a.ease === "linear" ? p : smooth(p);
      return Object.fromEntries(Object.keys(a.value).map((k) => [k, mix(a.value[k], b.value[k], q)]));
    };
  }
  var cameraTrack = (keys) => track(keys);
  function settle(t, contact, amplitude = 1, decay = 6, hz = 3) {
    const dt = t - contact;
    return dt < 0 ? 0 : amplitude * Math.exp(-decay * dt) * Math.sin(dt * Math.PI * 2 * hz);
  }
  function hingeRise(t, start, end, base, lean = 0) {
    const p = smooth(clamp((t - start) / Math.max(1e-6, end - start)));
    return {
      ...base,
      rotation: lean * (1 - p),
      squash: Math.sin(p * Math.PI / 2),
      opacity: p > 0 ? 1 : 0,
      scale: 1
    };
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
  function pointAt(path, fraction) {
    const d = clamp(fraction) * path.length;
    const s = path.segments.find((s2) => s2.start + s2.length >= d) || path.segments.at(-1);
    if (!s) return { ...path.origin };
    const p = clamp((d - s.start) / s.length);
    return { x: mix(s.a.x, s.b.x, p), y: mix(s.a.y, s.b.y, p) };
  }
  function trace(g, path, fraction) {
    const d = clamp(fraction) * path.length;
    g.beginPath();
    for (const s of path.segments) {
      if (s.start >= d) break;
      if (s.move) g.moveTo(s.a.x, s.a.y);
      const p = Math.min(1, (d - s.start) / s.length);
      g.lineTo(mix(s.a.x, s.b.x, p), mix(s.a.y, s.b.y, p));
      if (p < 1) break;
    }
    g.stroke();
  }

  // src/kit/materials.ts
  function grain(g, w, h, seed2 = 1, amount = 0.08, density = 450) {
    g.save();
    for (let i = 0; i < density; i++) {
      g.fillStyle = i % 3 ? `rgba(73,61,43,${amount})` : `rgba(255,255,244,${amount})`;
      const x = (hash(seed2 + i * 7) - 0.5) * w, y = (hash(seed2 + i * 11) - 0.5) * h;
      g.fillRect(x, y, 0.6 + hash(i) * 2.2, 0.5 + hash(i + 33) * 0.8);
    }
    g.restore();
  }
  function tape(s, pose, w = 58, seed2 = 1) {
    s.group(pose, () => {
      const g = s.g;
      s.shadow(0.4);
      s.edge(-w / 2, -10, w, 20, seed2, 3.5);
      g.fillStyle = "rgba(237,201,129,.62)";
      g.fill();
      g.shadowColor = "transparent";
      g.strokeStyle = "rgba(255,252,231,.4)";
      g.lineWidth = 0.7;
      g.stroke();
      grain(g, w, 18, seed2, 0.1, 50);
    });
  }
  function cutout(s, pose, contour, color, seed2 = 1, lift = 3) {
    s.group(pose, () => {
      const g = s.g;
      const shape = () => {
        g.beginPath();
        contour.forEach((p, i) => i ? g.lineTo(p.x, p.y) : g.moveTo(p.x, p.y));
        g.closePath();
      };
      s.shadow(lift);
      shape();
      g.fillStyle = color;
      g.fill();
      g.shadowColor = "transparent";
      g.strokeStyle = "rgba(255,249,230,.8)";
      g.lineWidth = 2;
      g.stroke();
      const xs = contour.map((p) => p.x), ys = contour.map((p) => p.y);
      const bounds = { x: Math.min(...xs), y: Math.min(...ys), w: Math.max(...xs) - Math.min(...xs), h: Math.max(...ys) - Math.min(...ys) };
      s.clip(shape, bounds, () => {
        g.translate(bounds.x + bounds.w / 2, bounds.y + bounds.h / 2);
        grain(g, bounds.w, bounds.h, seed2, 0.1);
      });
      s.bounds(bounds);
    });
  }
  function tornEllipse(rx, ry, seed2 = 1, rough = 2) {
    return Array.from({ length: 72 }, (_, i) => {
      const a = i * Math.PI * 2 / 72, d = (hash(seed2 + i) - 0.5) * rough;
      return { x: Math.cos(a) * (rx + d), y: Math.sin(a) * (ry + d) };
    });
  }
  function halftone(g, w, h, color, spacing = 9, radius = 1.7) {
    g.save();
    g.fillStyle = color;
    for (let y = -h / 2; y < h / 2; y += spacing) for (let x = -w / 2; x < w / 2; x += spacing) {
      g.beginPath();
      g.arc(x + (Math.round(y / spacing) & 1 ? spacing / 2 : 0), y, radius, 0, Math.PI * 2);
      g.fill();
    }
    g.restore();
  }
  function wash(g, contour, color, p, seed2 = 1) {
    const xs = contour.map((p2) => p2.x), ys = contour.map((p2) => p2.y);
    const l = Math.min(...xs), r = Math.max(...xs), top = Math.min(...ys), bottom = Math.max(...ys);
    g.save();
    g.beginPath();
    contour.forEach((v, i) => i ? g.lineTo(v.x, v.y) : g.moveTo(v.x, v.y));
    g.closePath();
    g.clip();
    g.beginPath();
    g.rect(l, top, (r - l) * clamp(p), bottom - top);
    g.clip();
    g.fillStyle = color;
    const alpha = g.globalAlpha;
    for (let i = 0; i < 18; i++) {
      g.globalAlpha = alpha * (0.06 + hash(seed2 + i) * 0.06);
      g.beginPath();
      g.ellipse(
        l + (r - l) * (i + 0.5) / 18,
        (top + bottom) / 2 + (hash(seed2 + i + 90) - 0.5) * 12,
        (r - l) / 5,
        (bottom - top) * (0.42 + hash(i + seed2) * 0.08),
        (hash(i) - 0.5) * 0.1,
        0,
        Math.PI * 2
      );
      g.fill();
    }
    g.globalAlpha = alpha * 0.24;
    g.strokeStyle = color;
    g.lineWidth = 3;
    g.beginPath();
    contour.forEach((v, i) => i ? g.lineTo(v.x, v.y) : g.moveTo(v.x, v.y));
    g.closePath();
    g.stroke();
    g.globalAlpha = alpha * 0.25;
    g.fillStyle = "#fff8e5";
    for (let i = 0; i < 140; i++) g.fillRect(l + hash(i + seed2) * (r - l), top + hash(i * 13 + seed2) * (bottom - top), 2 + hash(i) * 8, 0.8);
    g.restore();
  }

  // score.json
  var score_default = {
    fps: 24,
    duration: 52,
    shots: [
      {
        id: "collage",
        title: "\u7EB8\u62FC\u8D34",
        start: 0,
        end: 10,
        events: {
          travel: 1,
          plant: 3.1,
          bloom: 6.7
        },
        styleId: "paper_collage"
      },
      {
        id: "watercolor",
        title: "\u6C34\u5F69\u4E0E\u58A8",
        start: 10,
        end: 17,
        events: {
          ink: 2.4,
          wash: 1.5,
          bloom: 4.6
        },
        styleId: "watercolor_ink"
      },
      {
        id: "line_art",
        title: "\u7EBF\u6761",
        start: 17,
        end: 24,
        events: {
          draw: 0.4,
          complete: 4.5
        },
        styleId: "line_art"
      },
      {
        id: "scientific_diagram",
        title: "\u79D1\u5B66\u56FE\u793A",
        start: 24,
        end: 31,
        events: {
          focus: 1.8,
          focused: 3.3
        },
        styleId: "scientific_diagram"
      },
      {
        id: "whiteboard",
        title: "\u767D\u677F",
        start: 31,
        end: 38,
        events: {
          draw: 0.3,
          complete: 3.5,
          circle: 3.8,
          wipe: 5.5
        },
        styleId: "whiteboard"
      },
      {
        id: "risograph",
        title: "Riso",
        start: 38,
        end: 45,
        events: {
          blue: 0.5,
          red: 2.3,
          registered: 4.8
        },
        styleId: "risograph"
      },
      {
        id: "paper_popup",
        title: "\u7EB8\u7ACB\u4F53\u4E66",
        start: 45,
        end: 52,
        events: {
          open: 0.5,
          opened: 3.7
        },
        styleId: "paper_popup"
      }
    ],
    cues: [],
    sounds: [
      {
        shot: "collage",
        event: "plant",
        kind: "tap",
        gain: 0.75
      },
      {
        shot: "collage",
        event: "bloom",
        kind: "paper",
        gain: 0.8
      },
      {
        shot: "watercolor",
        event: "wash",
        kind: "brush",
        gain: 0.7
      },
      {
        shot: "line_art",
        event: "draw",
        kind: "pencil",
        gain: 0.5
      },
      {
        shot: "whiteboard",
        event: "circle",
        kind: "marker",
        gain: 0.5
      },
      {
        shot: "whiteboard",
        event: "wipe",
        kind: "wipe",
        gain: 0.55
      },
      {
        shot: "risograph",
        event: "red",
        kind: "print",
        gain: 0.6
      },
      {
        shot: "paper_popup",
        event: "open",
        kind: "fold",
        gain: 0.7
      }
    ],
    style: {
      styleId: "mixed_style_study",
      renderer: "canvas2d"
    }
  };

  // src/main.ts
  var score = score_default;
  var palette = { ink: "#304c49", moss: "#67855b", lime: "#b8bd75", rust: "#b97153", cream: "#f3e7cc" };
  var stemCommands = [
    { op: "M", x: 0, y: 0 },
    { op: "C", c1x: 4, c1y: -70, c2x: -12, c2y: -126, x: 2, y: -215 },
    { op: "M", x: 0, y: -92 },
    { op: "Q", cx: -70, cy: -99, x: -104, y: -154 },
    { op: "M", x: 1, y: -157 },
    { op: "Q", cx: 68, cy: -157, x: 112, y: -221 }
  ];
  var stem = measurePath(stemCommands);
  var leaf = (side, seed2 = 1) => Array.from({ length: 50 }, (_, i) => {
    const a = i * Math.PI * 2 / 50, r = 1 + Math.sin(a * 2) * 0.06 + Math.sin(i * 19 + seed2) * 0.02;
    return { x: side * (48 + Math.cos(a) * 49) * r, y: -24 + Math.sin(a) * 25 * r - Math.cos(a) * 26 };
  });
  function inkStem(g, p = 1, color = palette.ink, width = 4) {
    g.save();
    g.strokeStyle = color;
    g.lineWidth = width;
    g.lineCap = "round";
    g.lineJoin = "round";
    trace(g, stem, p);
    g.restore();
  }
  function vein(g, side) {
    g.save();
    g.strokeStyle = "#f1e4bd99";
    g.lineWidth = 1.7;
    g.beginPath();
    g.moveTo(0, 0);
    g.quadraticCurveTo(side * 45, -26, side * 93, -48);
    g.stroke();
    for (let j = 1; j < 5; j++) {
      g.beginPath();
      g.moveTo(side * j * 18, -j * 9);
      g.lineTo(side * (j * 18 + 8), -j * 9 - 14);
      g.stroke();
    }
    g.restore();
  }
  function seed(s, x, y, scale = 1, color = "#b97a51") {
    cutout(s, { x, y, rotation: -0.38, scale }, tornEllipse(17, 26, 33, 1.2), color, 8, 1.5);
    s.group({ x, y, rotation: -0.38, scale }, () => {
      const g = s.g;
      g.strokeStyle = "#69482c99";
      g.lineWidth = 1.4;
      g.beginPath();
      g.moveTo(-3, -14);
      g.quadraticCurveTo(8, 2, 0, 18);
      g.stroke();
    });
  }
  function pot(s, x, y, front = false) {
    const points = front ? [{ x: -90, y: -15 }, { x: 88, y: -15 }, { x: 68, y: 115 }, { x: -68, y: 115 }] : [{ x: -91, y: -18 }, { x: 90, y: -18 }, { x: 82, y: 20 }, { x: -83, y: 20 }];
    cutout(s, { x, y }, points, front ? palette.rust : "#4e4939", 19, 2);
    if (front) s.group({ x, y }, () => {
      const g = s.g;
      g.strokeStyle = "#edd0a799";
      g.lineWidth = 2;
      g.beginPath();
      g.moveTo(-62, 10);
      g.lineTo(-49, 92);
      g.moveTo(64, 9);
      g.lineTo(51, 92);
      g.stroke();
      tape(s, { x: 0, y: 40, rotation: -0.08 }, 46, 16);
    });
  }
  function heading(s, clean, label, sub) {
    if (clean) return;
    s.text(label, 100, 57, 29, palette.ink, { align: "left", weight: 600 });
    s.text(sub, 100, 93, 18, "#736b5c", { align: "left", weight: 400 });
  }
  var push = cameraTrack([
    { time: 0, value: { x: 640, y: 302.4, zoom: 1 } },
    { time: 4, value: { x: 654, y: 310, zoom: 1.055 } },
    { time: 8, value: { x: 656, y: 306, zoom: 1.055 } }
  ]);
  var shots = [
    { id: "collage", camera: ({ t }) => push(t), render({ stage: s, t, beat, clean }) {
      const g = s.g, qt = onTwos(t), arrive = beat.events.plant;
      s.paper({ x: 337, y: 352, w: 175, h: 230, rotation: -0.13, color: "#d9c795", seed: 44, name: "seed-packet" });
      s.group({ x: 337, y: 352, rotation: -0.13 }, () => {
        cutout(s, { x: 0, y: -27 }, leaf(1, 12), palette.moss, 11);
        tape(s, { x: 4, y: -109, rotation: 0.13 }, 66, 22);
      });
      pot(s, 669, 425);
      const p = arc({ x: 355, y: 305 }, { x: 669, y: 427 }, phase(qt, beat.events.travel, arrive), 125);
      if (t < arrive) seed(s, p.x, p.y, 1.2);
      s.group({ x: 669, y: 426, rotation: settle(qt, arrive, 0.025) }, () => {
        const growth = phase(qt, arrive + 0.2, beat.events.bloom);
        inkStem(g, growth, palette.moss, 6);
        const openL = phase(qt, arrive + 0.75, arrive + 1.8), openR = phase(qt, arrive + 1.4, beat.events.bloom);
        s.group({ x: 0, y: -93, rotation: (1 - openL) * 0.8, scale: Math.max(0.01, openL) }, () => {
          cutout(s, { x: 0, y: 0 }, leaf(-1, 2), palette.moss, 3);
          vein(g, -1);
        });
        s.group({ x: 0, y: -157, rotation: -(1 - openR) * 0.8, scale: Math.max(0.01, openR) }, () => {
          cutout(s, { x: 0, y: 0 }, leaf(1, 6), palette.lime, 6);
          vein(g, 1);
        });
      });
      pot(s, 669, 425, true);
      cutout(s, { x: 1040, y: 560, rotation: 0.35, scale: 1.6 }, leaf(-1, 77), "#536f60", 77, 8);
      s.group({ x: 928, y: 490, rotation: 0.18 }, () => {
        cutout(s, { x: 0, y: 0 }, tornEllipse(56, 18, 81), "#a9bac0", 55, 4);
        cutout(s, { x: 55, y: 0 }, [{ x: 0, y: -7 }, { x: 100, y: -7 }, { x: 107, y: 8 }, { x: 0, y: 8 }], "#a98459", 42, 3);
      });
      heading(s, clean, "\u7EB8\u62FC\u8D34 \xB7 \u4E00\u7C92\u79CD\u5B50\u7684\u65C5\u7A0B", "\u7269\u4EF6\u63A5\u89E6\u3001\u906E\u6321\u4E0E\u5C55\u5F00\uFF0C\u8BA9\u753B\u9762\u81EA\u5DF1\u8BB2\u6545\u4E8B");
    } },
    { id: "watercolor", render({ stage: s, t, beat, clean }) {
      const g = s.g;
      g.fillStyle = "#f6efd9";
      g.fillRect(0, 0, s.width, s.height);
      s.group({ x: 640, y: 462 }, () => {
        wash(g, [{ x: -105, y: -8 }, { x: 105, y: -8 }, { x: 71, y: 110 }, { x: -72, y: 110 }], "#ad6548", phase(t, 0, 0.9), 3);
        inkStem(g, phase(t, 0.65, beat.events.ink), "#657460", 2.5);
        s.group({ x: 0, y: -93 }, () => wash(g, leaf(-1), "#507561", phase(t, beat.events.wash, 3.3), 22));
        s.group({ x: 0, y: -157 }, () => wash(g, leaf(1), "#99a449", phase(t, 2.6, beat.events.bloom), 33));
        s.group({ x: 0, y: 10 }, () => wash(g, tornEllipse(77, 15, 28), "#665347", phase(t, 0.4, 1.1), 9));
        g.save();
        g.strokeStyle = "#86614b";
        g.globalAlpha = 0.45;
        g.lineWidth = 1.6;
        g.beginPath();
        g.moveTo(-100, -6);
        g.lineTo(-71, 109);
        g.lineTo(69, 108);
        g.lineTo(101, -6);
        g.stroke();
        g.restore();
        if (t > 3.3) s.group({ x: 0, y: -93 }, () => vein(g, -1));
      });
      s.group({ x: 865, y: 538, rotation: -0.5 }, () => {
        cutout(s, { x: 0, y: 0 }, [{ x: -7, y: -130 }, { x: 7, y: -130 }, { x: 5, y: 0 }, { x: -5, y: 0 }], "#ab855a", 1, 1);
        cutout(s, { x: 0, y: -137 }, tornEllipse(8, 26, 9), "#665347", 2, 1);
      });
      heading(s, clean, "\u6C34\u5F69\u4E0E\u58A8 \xB7 \u751F\u957F\u7559\u4E0B\u7B14\u89E6", "\u9010\u7B14\u53E0\u8272\u3001\u79EF\u8272\u8FB9\u7F18\u4E0E\u5E72\u5237\uFF0C\u800C\u975E\u6574\u56FE\u6DE1\u5165");
    } },
    { id: "line_art", camera: ({ t }) => cameraTrack([
      { time: 0, value: { x: 640, y: 302.4, zoom: 1 } },
      { time: 3, value: { x: 640, y: 286, zoom: 1.12 } },
      { time: 7, value: { x: 640, y: 302.4, zoom: 1 } }
    ])(t), render({ stage: s, t, beat, clean }) {
      const g = s.g;
      seed(s, 640, 550, 0.75);
      const line = measurePath([
        { op: "M", x: 565, y: 520 },
        { op: "L", x: 540, y: 417 },
        { op: "Q", cx: 640, cy: 387, x: 740, y: 417 },
        { op: "L", x: 715, y: 520 },
        { op: "Q", cx: 640, cy: 541, x: 565, y: 520 },
        { op: "M", x: 640, y: 419 },
        { op: "C", c1x: 650, c1y: 343, c2x: 619, c2y: 287, x: 642, y: 206 },
        { op: "C", c1x: 570, c1y: 295, c2x: 553, c2y: 346, x: 640, y: 327 },
        { op: "C", c1x: 726, c1y: 307, c2x: 738, c2y: 235, x: 642, y: 267 }
      ]);
      const p = phase(t, beat.events.draw, beat.events.complete);
      g.strokeStyle = palette.ink;
      g.lineWidth = 3.8;
      g.lineCap = "round";
      g.lineJoin = "round";
      trace(g, line, p);
      if (p > 0 && p < 1) {
        const tip = pointAt(line, p);
        g.fillStyle = palette.rust;
        g.beginPath();
        g.arc(tip.x, tip.y, 4, 0, Math.PI * 2);
        g.fill();
      }
      s.bounds({ x: 540, y: 203, w: 204, h: 340, name: "drawn-plant" });
      heading(s, clean, "\u7EBF\u6761 \xB7 \u4E00\u7B14\u5EFA\u7ACB\u5173\u7CFB", "\u6309\u8DEF\u5F84\u957F\u5EA6\u524D\u8FDB\uFF0C\u62AC\u7B14\u5904\u4E0D\u4EA7\u751F\u65E0\u610F\u4E49\u8FDE\u63A5\u7EBF");
    } },
    { id: "scientific_diagram", render({ stage: s, t, beat, clean }) {
      const g = s.g, focus = phase(t, beat.events.focus, beat.events.focused);
      s.group({ x: 540, y: 430 }, () => {
        inkStem(g, 1, palette.moss, 4);
        cutout(s, { x: 0, y: -93 }, leaf(-1), palette.moss, 23, 0);
        cutout(s, { x: 0, y: -157 }, leaf(1), palette.lime, 28, 0);
        g.fillStyle = "#9c765b";
        g.beginPath();
        g.moveTo(-90, -10);
        g.lineTo(90, -10);
        g.lineTo(68, 110);
        g.lineTo(-68, 110);
        g.closePath();
        g.fill();
        const root = measurePath([
          { op: "M", x: 0, y: 0 },
          { op: "Q", cx: 4, cy: 40, x: -16, y: 95 },
          { op: "M", x: 0, y: 30 },
          { op: "Q", cx: 39, cy: 40, x: 48, y: 78 },
          { op: "M", x: -7, y: 60 },
          { op: "Q", cx: -35, cy: 66, x: -45, y: 90 }
        ]);
        g.strokeStyle = "#e9dcc1";
        g.lineWidth = 3;
        trace(g, root, 1);
        for (let i = 0; i < 4; i++) {
          const p = pointAt(root, 1 - (t * 0.22 + i / 4) % 1);
          g.fillStyle = "#89bbca";
          g.beginPath();
          g.arc(p.x, p.y, 3, 0, Math.PI * 2);
          g.fill();
        }
      });
      if (focus > 0) {
        g.save();
        g.globalAlpha = focus;
        g.strokeStyle = "#7c9da3";
        g.lineWidth = 1.5;
        g.beginPath();
        g.moveTo(570, 450);
        g.lineTo(775, 395);
        g.stroke();
        s.group({ x: 891, y: 368, scale: 0.85 + 0.15 * focus }, () => {
          g.fillStyle = "#f1ecda";
          g.beginPath();
          g.arc(0, 0, 105, 0, Math.PI * 2);
          g.fill();
          g.stroke();
          g.save();
          g.clip();
          g.strokeStyle = "#c9b7a0";
          g.lineWidth = 1.4;
          for (let i = -3; i < 4; i++) for (let j = -3; j < 4; j++) {
            g.strokeRect(i * 46 + j % 2 * 23, j * 40, 43, 37);
          }
          g.strokeStyle = "#7f9e8a";
          g.lineWidth = 20;
          g.beginPath();
          g.moveTo(0, 110);
          g.lineTo(0, -110);
          g.stroke();
          for (let i = 0; i < 5; i++) {
            const y = 105 - (t * 60 + i * 44) % 220;
            g.fillStyle = "#6da8bb";
            g.beginPath();
            g.arc(0, y, 5, 0, Math.PI * 2);
            g.fill();
          }
          g.restore();
        });
        g.restore();
      }
      heading(s, clean, "\u79D1\u5B66\u56FE\u793A \xB7 \u5C40\u90E8\u624D\u9700\u8981\u89E3\u91CA", "\u5207\u9762\u3001\u5B9A\u4F4D\u4E0E\u5C40\u90E8\u653E\u5927\uFF1B\u7D20\u6750\u610F\u4E49\u4ECD\u9700\u4E13\u4E1A\u5BA1\u67E5");
    } },
    { id: "whiteboard", render({ stage: s, t, beat, clean }) {
      const g = s.g;
      g.fillStyle = "#f7f6ef";
      g.fillRect(0, 0, s.width, s.height);
      seed(s, 640, 566, 0.6);
      const potLine = measurePath([{ op: "M", x: 550, y: 440 }, { op: "L", x: 730, y: 440 }, { op: "L", x: 706, y: 541 }, { op: "L", x: 577, y: 541 }, { op: "L", x: 550, y: 440 }]);
      const p = phase(t, beat.events.draw, 1.4);
      g.strokeStyle = "#375b60";
      g.lineWidth = 5;
      g.lineCap = "round";
      trace(g, potLine, p);
      s.group({ x: 640, y: 440 }, () => {
        inkStem(g, phase(t, 1.2, 2.5), "#557b51", 5);
        for (const [side, y] of [[-1, -93], [1, -157]]) {
          const outline = measurePath(leaf(side).map((p2, i) => ({ op: i === 0 ? "M" : "L", x: p2.x, y: p2.y })));
          s.group({ x: 0, y }, () => trace(g, outline, phase(t, side < 0 ? 2.3 : 2.7, beat.events.complete)));
        }
      });
      const ring = measurePath([
        { op: "M", x: 528, y: 262 },
        { op: "C", c1x: 504, c1y: 140, c2x: 792, c2y: 122, x: 784, y: 296 },
        { op: "C", c1x: 730, c1y: 380, c2x: 526, c2y: 369, x: 528, y: 262 }
      ]);
      g.strokeStyle = "#b76c45";
      g.lineWidth = 3;
      trace(g, ring, phase(t, beat.events.circle, 4.9));
      if (t > beat.events.wipe) {
        g.save();
        g.beginPath();
        g.rect(490, 120, 340 * phase(t, beat.events.wipe, 6.7), 255);
        g.clip();
        g.fillStyle = "#f7f6ef";
        g.fillRect(490, 120, 340, 255);
        g.restore();
      }
      s.bounds({ x: 510, y: 163, w: 280, h: 384, name: "marker-plant" });
      heading(s, clean, "\u767D\u677F \xB7 \u5148\u5EFA\u7ACB\uFF0C\u518D\u805A\u7126", "\u7B14\u987A\u3001\u5F3A\u8C03\u4E0E\u6709\u76EE\u7684\u7684\u64E6\u9664\uFF1B\u65E0\u9700\u60AC\u6D6E\u624B\u638C");
    } },
    { id: "risograph", render({ stage: s, t, beat, clean }) {
      const g = s.g;
      g.fillStyle = "#ede5cf";
      g.fillRect(0, 0, s.width, s.height);
      seed(s, 459, 522, 0.75, "#b88757");
      s.group({ x: 640, y: 444 }, () => {
        const blue = phase(t, beat.events.blue, 2), red = phase(t, beat.events.red, beat.events.registered);
        const plate = (color, offset, p) => {
          g.save();
          g.translate(offset.x, offset.y);
          g.beginPath();
          g.rect(-150, -285, 300 * p, 430);
          g.clip();
          g.globalAlpha *= 0.76;
          g.fillStyle = color;
          g.beginPath();
          g.moveTo(-92, 0);
          g.lineTo(92, 0);
          g.lineTo(68, 112);
          g.lineTo(-68, 112);
          g.closePath();
          g.fill();
          inkStem(g, 1, color, 6);
          for (const [side, y] of [[-1, -93], [1, -157]]) {
            g.save();
            g.translate(0, y);
            g.beginPath();
            leaf(side).forEach((p2, i) => i ? g.lineTo(p2.x, p2.y) : g.moveTo(p2.x, p2.y));
            g.closePath();
            g.clip();
            g.fillStyle = color;
            g.globalAlpha = 0.62;
            g.fillRect(-110, -90, 220, 130);
            g.globalAlpha = 1;
            halftone(g, 220, 180, color, 8, 1.7);
            g.restore();
          }
          g.restore();
        };
        plate("#508d9b", { x: -2.5, y: 0 }, blue);
        g.save();
        g.globalCompositeOperation = "multiply";
        plate("#e29763", { x: 3.5, y: 2.2 }, red);
        g.restore();
        grain(g, 330, 410, 271, 0.08, 500);
      });
      heading(s, clean, "Riso \xB7 \u4E24\u5F20\u8272\u7248\u76F8\u9047", "\u56FA\u5B9A\u5957\u5370\u504F\u5DEE\u3001\u534A\u8272\u8C03\u4E0E\u53E0\u8272\uFF1B\u9519\u7248\u4E0D\u9010\u5E27\u4E71\u8DF3");
    } },
    { id: "paper_popup", camera: ({ t }) => cameraTrack([
      { time: 0, value: { x: 640, y: 302.4, zoom: 1 } },
      { time: 3, value: { x: 640, y: 322, zoom: 1.065 } },
      { time: 7, value: { x: 640, y: 322, zoom: 1.065 } }
    ])(t), render({ stage: s, t, beat, clean }) {
      const g = s.g, p = phase(t, beat.events.open, beat.events.opened);
      s.group({ x: 640, y: 511 }, () => {
        s.paper({ x: -173, y: 0, w: 350, h: 155, rotation: -0.08, color: "#ead7b3", seed: 8, name: "left-page" });
        s.paper({ x: 173, y: 0, w: 350, h: 155, rotation: 0.08, color: "#f3e5c8", seed: 19, name: "right-page" });
        g.strokeStyle = "#bda27b";
        g.lineWidth = 2;
        g.beginPath();
        g.moveTo(0, -76);
        g.lineTo(0, 75);
        g.stroke();
        const risen = hingeRise(t, beat.events.open, beat.events.opened, { x: 0, y: -14 });
        g.save();
        g.translate(risen.x, risen.y);
        g.scale(1, risen.squash);
        g.globalAlpha = risen.opacity ?? 1;
        cutout(s, { x: 0, y: -123 }, [{ x: -177, y: 109 }, { x: -177, y: -128 }, { x: 0, y: -214 }, { x: 177, y: -128 }, { x: 177, y: 109 }], "#acbba4", 56, 9);
        g.strokeStyle = "#f4e8ce";
        g.lineWidth = 6;
        g.beginPath();
        g.moveTo(-137, -12);
        g.lineTo(-137, -118);
        g.lineTo(0, -184);
        g.lineTo(137, -118);
        g.lineTo(137, -12);
        g.moveTo(0, -184);
        g.lineTo(0, -13);
        g.moveTo(-138, -91);
        g.lineTo(138, -91);
        g.stroke();
        g.restore();
        s.group({ x: 0, y: -3, scale: 1 }, () => {
          g.save();
          g.scale(1, Math.sin(p * Math.PI / 2));
          inkStem(g, 1, palette.moss, 5);
          cutout(s, { x: 0, y: -93 }, leaf(-1), palette.moss, 34, 7);
          cutout(s, { x: 0, y: -157 }, leaf(1), palette.lime, 35, 7);
          g.restore();
        });
        cutout(s, { x: 0, y: 0 }, [{ x: -85, y: 0 }, { x: 85, y: 0 }, { x: 63, y: 54 }, { x: -63, y: 54 }], palette.rust, 78, 5);
        tape(s, { x: -72, y: 22, rotation: -0.12 }, 40, 9);
        tape(s, { x: 73, y: 22, rotation: 0.12 }, 40, 10);
      });
      heading(s, clean, "\u7EB8\u7ACB\u4F53\u4E66 \xB7 \u7FFB\u5F00\u4E00\u4E2A\u5C0F\u4E16\u754C", "\u5E95\u90E8\u6298\u8F74\u3001\u56FA\u5B9A\u7EB8\u811A\u4E0E\u524D\u540E\u906E\u6321 \xB7 Canvas 2.5D \u6295\u5F71");
    } }
  ];
  mount({ assets: [], score, shots });
})();
//# sourceMappingURL=film.js.map
