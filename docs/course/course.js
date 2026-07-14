/* ===========================================================================
   ESP32-S3 Lab · course behaviour (shared)
   Productised from the Day 26 prototype and made data-driven. The page injects
   its data as JSON:
     - a lesson page has  <script id="lesson-data">  (explainers, day, prev/next)
     - the course map has <script id="course-data">  (published days)
   Behaviours: accessible <dialog> explainers + image zoom, code-language tabs,
   checkable build steps with localStorage progress + completion, scroll-spy
   rail, prev/next day nav, the hero instrument readout, and the copy-prompt
   toast. Progress is client-side only — never a gate.
   =========================================================================== */

function readJSON(id) {
  const el = document.getElementById(id);
  if (!el) return null;
  try {
    return JSON.parse(el.textContent);
  } catch {
    return null;
  }
}

const lessonData = readJSON("lesson-data");
const courseData = readJSON("course-data");

/* --------------------------------------------------------------------------
   Progress store (localStorage) — per-day step state + whole-day completion
   -------------------------------------------------------------------------- */
const progress = {
  dayKey: (day) => `tinyskiff.day.${day}`,
  resumeKey: "tinyskiff.resume",
  get(day) {
    try {
      return JSON.parse(localStorage.getItem(this.dayKey(day))) || {};
    } catch {
      return {};
    }
  },
  set(day, value) {
    try {
      localStorage.setItem(this.dayKey(day), JSON.stringify(value));
    } catch {
      /* storage unavailable (private mode) — progress simply won't persist */
    }
  },
  isDone(day) {
    return this.get(day).done === true;
  },
  setResume(day) {
    try {
      localStorage.setItem(this.resumeKey, String(day));
    } catch {
      /* ignore */
    }
  },
  getResume() {
    try {
      const raw = localStorage.getItem(this.resumeKey);
      return raw ? Number(raw) : null;
    } catch {
      return null;
    }
  },
};

/* --------------------------------------------------------------------------
   Lightbox explainer dialog (data from the injected explainers map)
   -------------------------------------------------------------------------- */
const explainers = (lessonData && lessonData.explainers) || {};
const explainerDialog = document.querySelector("#explainer");
const explainerTitle = document.querySelector("#explainerTitle");
const explainerBody = document.querySelector("#explainerBody");
const explainerShortcut = document.querySelector("#explainerShortcut");
let lastTrigger = null;

function openExplainer(trigger) {
  const item = explainers[trigger.dataset.topic];
  if (!item || !explainerDialog) return;
  lastTrigger = trigger;
  explainerTitle.textContent = item.title;
  explainerBody.textContent = item.body;
  explainerShortcut.textContent = item.shortcut;
  showDialog(explainerDialog);
}

document.querySelectorAll(".define").forEach((btn) => {
  // define chips inside a .step button must not toggle the step
  btn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    openExplainer(btn);
  });
});

/* --------------------------------------------------------------------------
   Image zoom dialog
   -------------------------------------------------------------------------- */
const imageBox = document.querySelector("#imageBox");
const imageBoxImg = document.querySelector("#imageBoxImg");
const imageBoxCap = document.querySelector("#imageBoxCap");

document.querySelectorAll("[data-zoom]").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (!imageBox) return;
    lastTrigger = btn;
    imageBoxImg.src = btn.dataset.zoom;
    imageBoxImg.alt = btn.querySelector("img")?.alt || "";
    imageBoxCap.textContent = btn.dataset.cap || "";
    showDialog(imageBox);
  });
});

/* --------------------------------------------------------------------------
   Dialog helpers — open, close, backdrop click, focus return
   -------------------------------------------------------------------------- */
function showDialog(dialog) {
  if (typeof dialog.showModal === "function") {
    dialog.showModal();
  } else {
    dialog.setAttribute("open", "");
  }
  dialog.querySelector("[data-close]")?.focus();
}

function closeDialog(dialog) {
  if (dialog.open) dialog.close();
  if (lastTrigger) {
    lastTrigger.focus();
    lastTrigger = null;
  }
}

document.querySelectorAll("dialog.lightbox").forEach((dialog) => {
  dialog.querySelectorAll("[data-close]").forEach((btn) =>
    btn.addEventListener("click", () => closeDialog(dialog))
  );
  // click on the backdrop (outside the dialog's own box) closes it
  dialog.addEventListener("click", (e) => {
    const r = dialog.getBoundingClientRect();
    const inside =
      e.clientX >= r.left && e.clientX <= r.right &&
      e.clientY >= r.top && e.clientY <= r.bottom;
    if (!inside) closeDialog(dialog);
  });
  // native ESC (dialog 'cancel') — restore trigger focus
  dialog.addEventListener("cancel", () => {
    if (lastTrigger) { lastTrigger.focus(); lastTrigger = null; }
  });
});

/* --------------------------------------------------------------------------
   Code language tabs (Arduino / MicroPython)
   -------------------------------------------------------------------------- */
const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
function selectTab(tab) {
  tabs.forEach((t) => {
    const selected = t === tab;
    t.setAttribute("aria-selected", String(selected));
    const panel = document.querySelector("#" + t.getAttribute("aria-controls"));
    if (panel) panel.hidden = !selected;
  });
}
tabs.forEach((tab, i) => {
  tab.addEventListener("click", () => selectTab(tab));
  tab.addEventListener("keydown", (e) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    e.preventDefault();
    const next = e.key === "ArrowRight" ? (i + 1) % tabs.length : (i - 1 + tabs.length) % tabs.length;
    tabs[next].focus();
    selectTab(tabs[next]);
  });
});

/* --------------------------------------------------------------------------
   Checkable build steps + progress + completion + persistence
   -------------------------------------------------------------------------- */
const steps = Array.from(document.querySelectorAll(".step"));
const stepBar = document.querySelector("#stepBar");
const stepCount = document.querySelector("#stepCount");
const doneBanner = document.querySelector("#doneBanner");

function refreshSteps() {
  if (!steps.length) return;
  const state = steps.map((s) => s.classList.contains("done"));
  const done = state.filter(Boolean).length;
  if (stepBar) stepBar.style.width = (done / steps.length) * 100 + "%";
  if (stepCount) stepCount.textContent = `${done} / ${steps.length} done`;
  if (doneBanner) doneBanner.classList.toggle("show", done === steps.length);
  if (lessonData) {
    progress.set(lessonData.day, { steps: state, done: done === steps.length && steps.length > 0 });
  }
}

function toggleStep(step) {
  const done = step.classList.toggle("done");
  step.querySelector(".box").setAttribute("aria-pressed", String(done));
  refreshSteps();
}

if (steps.length) {
  // restore saved step state before wiring events
  if (lessonData) {
    const saved = progress.get(lessonData.day).steps || [];
    steps.forEach((step, i) => {
      if (saved[i]) {
        step.classList.add("done");
        step.querySelector(".box").setAttribute("aria-pressed", "true");
      }
    });
    progress.setResume(lessonData.day);
  }
  steps.forEach((step) => {
    step.querySelector(".box").addEventListener("click", () => toggleStep(step));
    step.querySelector(".text").addEventListener("click", (e) => {
      // A resource link inside the step text should open, not tick the step.
      if (e.target.closest("a")) return;
      toggleStep(step);
    });
  });
  refreshSteps();
}

/* --------------------------------------------------------------------------
   Scroll-spy rail
   -------------------------------------------------------------------------- */
const railLinks = Array.from(document.querySelectorAll(".rail-nav a"));
const spySections = railLinks
  .map((a) => document.querySelector(a.getAttribute("href")))
  .filter(Boolean);

if ("IntersectionObserver" in window && spySections.length) {
  const spy = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        railLinks.forEach((a) =>
          a.classList.toggle("active", a.getAttribute("href") === "#" + entry.target.id)
        );
      });
    },
    { rootMargin: "-45% 0px -50% 0px" }
  );
  spySections.forEach((s) => spy.observe(s));
}

/* --------------------------------------------------------------------------
   Course map — reflect completion, count, resume affordance
   -------------------------------------------------------------------------- */
if (courseData) {
  const total = courseData.totalDays || 30;
  let done = 0;
  document.querySelectorAll(".day-tile[data-day]").forEach((tile) => {
    const day = Number(tile.dataset.day);
    if (progress.isDone(day)) {
      tile.classList.add("is-done");
      done += 1;
    }
  });
  const doneCount = document.querySelector("#doneCount");
  if (doneCount) doneCount.textContent = String(done);
  const voyage = document.querySelector("#mapVoyage span");
  if (voyage) voyage.style.width = (done / total) * 100 + "%";

  const resume = progress.getResume();
  const resumeLink = document.querySelector("#mapResume");
  const slugs = courseData.slugs || {};
  if (resumeLink && resume && slugs[resume]) {
    resumeLink.hidden = false;
    resumeLink.href = `${slugs[resume]}/`;
    resumeLink.textContent = `Resume — Day ${resume} →`;
  }
}

/* --------------------------------------------------------------------------
   Hero instrument readout (sounder) — respects reduced motion
   -------------------------------------------------------------------------- */
const sounder = document.querySelector('.sounder[data-instrument="sounder"]');
const sounderValue = document.querySelector("#sounderValue");
const sounderTarget = document.querySelector("#sounderTarget");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if (sounder && sounderValue && !reduceMotion) {
  const unit = sounderValue.querySelector("small")?.textContent || "";
  const targets = [
    { px: 40, cm: 24 },
    { px: 66, cm: 18 },
    { px: 96, cm: 12 },
    { px: 58, cm: 20 },
    { px: 34, cm: 27 },
  ];
  let i = 0;
  let base = targets[0].cm;
  setInterval(() => {
    const wobble = (Math.sin(Date.now() / 700) + Math.sin(Date.now() / 313)) * 0.35;
    sounderValue.innerHTML = (base + wobble).toFixed(2) + `<small>${unit}</small>`;
  }, 140);
  setInterval(() => {
    i = (i + 1) % targets.length;
    if (sounderTarget) sounderTarget.style.right = targets[i].px + "px";
    base = targets[i].cm;
  }, 2600);
}

/* --------------------------------------------------------------------------
   Copy-prompt → toast
   -------------------------------------------------------------------------- */
const toast = document.querySelector("#toast");
document.querySelectorAll("[data-copy]").forEach((btn) => {
  btn.addEventListener("click", async () => {
    if (!toast) return;
    try {
      await navigator.clipboard.writeText(btn.dataset.copy);
      toast.textContent = "Prompt copied";
      toast.classList.add("show");
      setTimeout(() => toast.classList.remove("show"), 1700);
    } catch {
      toast.textContent = "Copy failed — select the prompt manually";
      toast.classList.add("show");
      setTimeout(() => toast.classList.remove("show"), 2400);
    }
  });
});

/* --------------------------------------------------------------------------
   Lesson chat widget — a floating "ask about this lesson" panel.
   Backed by a local model proxy (POST /api/chat in serve.py). The widget is
   BACKEND-AWARE: it health-checks GET /api/chat first and only mounts when a
   backend answers. So the identical generated build is safe on the public
   Cloudflare Pages host (no backend there -> no button, nothing broken) and
   lights up wherever this backend is served (the tailnet today; a
   Cloudflare-Access origin later) with no rebuild. Only mounts on lesson pages.
   -------------------------------------------------------------------------- */
async function initLessonChat() {
  // Only lesson pages carry lesson-data with a day; the course map does not.
  if (!lessonData || lessonData.day == null) return;

  function lessonTitle() {
    return (document.title || "this lesson")
      .replace(/\s*[—–|]\s*ESP32-S3 Lab.*$/i, "")
      .trim() || "this lesson";
  }

  // Structured lesson packet is the preferred context (mission, wiring, steps,
  // coaching notes, troubleshooting); fall back to the page text if it's absent.
  async function loadPacket() {
    if (!lessonData.lessonCode) return null;
    try {
      const res = await fetch(`../packets/${encodeURIComponent(lessonData.lessonCode)}.json`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }

  function lessonText() {
    const main = document.querySelector(".lesson-main") || document.querySelector("main") || document.body;
    return (main.innerText || "").replace(/\s+\n/g, "\n").trim().slice(0, 9000);
  }

  function progressSummary() {
    const total = lessonData.totalDays || 30;
    let done = 0;
    for (let d = 1; d <= total; d += 1) {
      if (progress.isDone(d)) done += 1;
    }
    return `Currently on Day ${lessonData.day} of ${total}. Days marked complete: ${done}.`;
  }

  // Minimal, safe rendering: escape HTML, then reveal `inline` and ```fenced``` code.
  function render(text) {
    const esc = (s) => s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
    const parts = text.split(/```(?:\w+)?\n?([\s\S]*?)```/g);
    return parts
      .map((part, i) =>
        i % 2
          ? `<pre><code>${esc(part.replace(/\n$/, ""))}</code></pre>`
          : esc(part).replace(/`([^`]+)`/g, "<code>$1</code>")
      )
      .join("");
  }

  const packet = await loadPacket();
  const history = [];
  let busy = false;

  const fab = document.createElement("button");
  fab.className = "lchat-fab";
  fab.type = "button";
  fab.innerHTML = '<span class="lchat-fab__icon" aria-hidden="true">💬</span> Ask about this lesson';
  fab.setAttribute("aria-label", "Ask a question about this lesson");

  const panel = document.createElement("section");
  panel.className = "lchat";
  panel.hidden = true;
  panel.setAttribute("aria-label", "Lesson chat");
  panel.innerHTML = `
    <div class="lchat__head">
      <div>
        <p class="lchat__title">Ask about ${lessonTitle().replace(/[<>&]/g, "")}</p>
        <p class="lchat__sub">ESP32 tutor · qwen3-coder · runs on Skipper's tailnet</p>
      </div>
      <button class="lchat__close" type="button" aria-label="Close chat">×</button>
    </div>
    <div class="lchat__log" role="log" aria-live="polite">
      <div class="lchat-msg lchat-msg--hint">Ask anything about this lesson — the wiring, the code, or a term you don't recognise. Nothing here touches your board.</div>
    </div>
    <form class="lchat__form">
      <textarea class="lchat__input" rows="1" placeholder="e.g. why does the LED need a resistor?" aria-label="Your question"></textarea>
      <button class="lchat__send" type="submit">Send</button>
    </form>`;

  document.body.append(fab, panel);

  const log = panel.querySelector(".lchat__log");
  const form = panel.querySelector(".lchat__form");
  const input = panel.querySelector(".lchat__input");
  const sendBtn = panel.querySelector(".lchat__send");

  function open() {
    panel.hidden = false;
    fab.hidden = true;
    input.focus();
  }
  function close() {
    panel.hidden = true;
    fab.hidden = false;
    fab.focus(); // return focus to the trigger, not the now-hidden panel
  }
  fab.addEventListener("click", open);
  panel.querySelector(".lchat__close").addEventListener("click", close);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !panel.hidden) close(); });

  function addMsg(role, text) {
    const el = document.createElement("div");
    el.className = `lchat-msg lchat-msg--${role}`;
    el.innerHTML = render(text);
    log.append(el);
    log.scrollTop = log.scrollHeight;
    return el;
  }

  async function ask(question) {
    if (busy || !question.trim()) return;
    busy = true;
    sendBtn.disabled = true;
    addMsg("user", question);
    history.push({ role: "user", content: question });
    const botEl = addMsg("bot", "…");
    let answer = "";
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lessonTitle: lessonTitle(),
          lessonPacket: packet,
          lessonText: packet ? undefined : lessonText(),
          progress: progressSummary(),
          messages: history,
        }),
      });
      if (!res.ok || !res.body) throw new Error(`server responded ${res.status}`);
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        answer += decoder.decode(value, { stream: true });
        botEl.innerHTML = render(answer);
        log.scrollTop = log.scrollHeight;
      }
      history.push({ role: "assistant", content: answer });
    } catch (err) {
      botEl.innerHTML = render(`Sorry — I couldn't reach the model. (${err.message})`);
    } finally {
      busy = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = input.value;
    input.value = "";
    input.style.height = "auto";
    ask(q);
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
  });
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 112) + "px";
  });
}

// Backend-aware mount: only wire the widget in if our chat backend answers.
// A static host (e.g. Cloudflare Pages) serves its HTML fallback with 200 for
// unknown routes, so res.ok alone is NOT enough — require serve.py's sentinel
// header, which a static fallback can't produce. Keeps the public build clean.
(async () => {
  try {
    const res = await fetch("/api/chat", { method: "GET" });
    if (res.ok && res.headers.get("X-Lesson-Chat") === "ok") initLessonChat();
  } catch {
    /* no backend (e.g. the public static host) — no chat button, nothing broken */
  }
})();
