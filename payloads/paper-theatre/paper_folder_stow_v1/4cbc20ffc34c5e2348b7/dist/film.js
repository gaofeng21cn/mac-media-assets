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
  function caption(s, score, t) {
    const c = score.cues.find((c2) => t >= c2.start && t < c2.end);
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
    const canvas = document.querySelector("#film"), s = new Stage(canvas.getContext("2d"), canvas.width, canvas.height), score = config.score;
    const clean = new URLSearchParams(location.search).has("clean");
    const controls = document.querySelector("nav"), audio = document.querySelector("#voice"), play = document.querySelector("#play"), seek = document.querySelector("#seek");
    const chooser = document.createElement("select");
    chooser.setAttribute("aria-label", "\u9009\u62E9\u955C\u5934");
    chooser.innerHTML = '<option value="all">\u6574\u7247</option>' + score.shots.map((b) => `<option value="${b.id}">${b.title}</option>`).join("");
    controls.append(chooser);
    const initialShot = new URLSearchParams(location.search).get("shot");
    if (score.shots.some((b) => b.id === initialShot)) chooser.value = initialShot;
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
      const b = score.shots.find((b2) => b2.id === chooser.value);
      return b ? [b.start, b.end] : [0, score.duration];
    };
    function draw(time) {
      current = clamp(time, 0, score.duration - 1e-6);
      const i = Math.max(
        0,
        score.shots.findIndex((b) => current >= b.start && current < b.end)
      );
      const beat = score.shots[i], shot = config.shots.find((s2) => s2.id === beat.id);
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
      const subtitle = !clean ? caption(s, score, current) : void 0;
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
      window.__styleId = beat.styleId || score.style?.appliedStyleId;
      seek.value = String(current / score.duration);
      clock.textContent = `${current.toFixed(2)} / ${score.duration.toFixed(2)} \u79D2`;
    }
    window.__seek = draw;
    window.__cuts = [...score.shots.map((s2) => s2.start), score.duration];
    window.__total = score.duration;
    window.__score = score;
    window.__kitVersion = "1.2.0";
    window.__rendererId = "canvas2d";
    window.__requestedStyleId = score.style?.styleId;
    window.__styleId = score.style?.appliedStyleId;
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
      if (current < start || current >= end - 1 / score.fps) draw(start);
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
      draw(Number(seek.value) * score.duration);
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
        draw(current + delta / score.fps);
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
        if (next >= end - 1 / score.fps) {
          if (loop.checked) {
            next = start;
            if (audio) {
              audio.currentTime = start;
              void audio.play();
            }
          } else {
            next = end - 1 / score.fps;
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

  // src/kit/props.ts
  function clipFastener(stage, x, y, angle = -0.1) {
    stage.group({ x, y, rotation: angle }, () => {
      const g = stage.g;
      stage.shadow(1);
      g.strokeStyle = "#8c8069";
      g.lineWidth = 3;
      g.beginPath();
      g.moveTo(-6, 15);
      g.lineTo(-6, -10);
      g.bezierCurveTo(-6, -22, 10, -22, 10, -10);
      g.lineTo(10, 15);
      g.bezierCurveTo(10, 24, -12, 24, -12, 12);
      g.lineTo(-12, -8);
      g.stroke();
    });
  }
  function paperFolder(stage, pose, width, openness, contents, options = {}) {
    const height = options.height ?? width * 0.57;
    const open = Math.max(0, Math.min(1, openness));
    stage.group(pose, () => {
      stage.paper({ x: 0, y: 0, w: width, h: height, color: options.color ?? "#6d8884", seed: 203, lift: 4, name: "case-folder" });
      stage.paper({ x: -width * 0.33, y: -height * 0.5, w: width * 0.27, h: 23, color: options.color ?? "#6d8884", seed: 204, lift: 1, name: "folder-tab" });
      stage.paper({ x: 0, y: 0, w: width * 0.94, h: height * 0.91, color: "#eee6d5", seed: 205, lift: 1, name: "folder-lining" });
      contents();
      stage.group({ x: -width * 0.5, y: 0 }, () => {
        const g = stage.g;
        g.scale(Math.max(0.018, Math.cos(open * Math.PI / 2)), 1);
        stage.paper({ x: width * 0.5, y: 0, w: width, h: height, color: options.color ?? "#74958f", seed: 209, lift: open * 5, name: "folder-cover" });
        g.save();
        g.shadowColor = "transparent";
        g.strokeStyle = "#e7dec599";
        g.lineWidth = 2;
        g.strokeRect(width * 0.34, -height * 0.19, width * 0.17, height * 0.33);
        for (let i = 0; i < 3; i++) {
          g.beginPath();
          g.moveTo(width * 0.375, -height * 0.1 + i * height * 0.065);
          g.lineTo(width * 0.475, -height * 0.1 + i * height * 0.065);
          g.stroke();
        }
        g.restore();
      });
    });
  }

  // score.json
  var score_default = {
    fps: 24,
    duration: 6,
    style: {
      styleId: "paper_collage",
      appliedStyleId: "paper_collage",
      renderer: "canvas2d"
    },
    shots: [
      {
        id: "folder",
        title: "\u6253\u5F00\u3001\u6536\u5165\u3001\u5939\u4F4F",
        start: 0,
        end: 6,
        events: {
          coverOpens: 2,
          recordsLand: 3.4,
          clipContacts: 4.1
        }
      }
    ],
    cues: [],
    sounds: []
  };

  // src/main.ts
  mount({ assets: [], score: score_default, shots: [{ id: "folder", render: ({ stage: s, t }) => {
    s.tracking = false;
    s.paper({ x: 640, y: 360, w: 1170, h: 630, color: "#d8d9c6", seed: 850, lift: 0 });
    s.tracking = true;
    paperFolder(s, { x: 640, y: 350, rotation: -0.015 }, 450, phase(t, 0.5, 2), () => {
      const q = phase(t, 2.1, 3.4);
      for (const side of [-1, 1]) s.group({ x: mix(side * 390, side * 107, q), y: mix(-70, 0, q), rotation: side * 0.045 }, () => {
        s.paper({ x: 0, y: 0, w: 152, h: 204, color: "#f1e7cc", seed: 860 + side, lift: 2, name: "document" });
        s.text(side < 0 ? "\u8BB0\u5F55" : "\u8BA1\u5212", 0, -60, 26, "#345a56");
        for (let i = 0; i < 3; i++) s.paper({ x: -35 + i * 36, y: 30, w: 16, h: 30 + i * 16, color: ["#b08462", "#809b91", "#c0aa69"][i], seed: 880 + i, lift: 0.2 });
      });
      clipFastener(s, -141, mix(-210, -92, phase(t, 3.6, 4.1)), -0.07);
    });
    s.text("\u6253\u5F00 \xB7 \u6536\u5165 \xB7 \u5939\u4F4F", 640, 617, 26, "#345a56");
  } }] });
})();
//# sourceMappingURL=film.js.map
