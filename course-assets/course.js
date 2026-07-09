/* ===========================================================================
   TinySkiff ESP32-S3 Lab · course behaviour (shared)
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
    const raw = localStorage.getItem(this.resumeKey);
    return raw ? Number(raw) : null;
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
    step.querySelector(".text").addEventListener("click", () => toggleStep(step));
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
