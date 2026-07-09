/* ===========================================================================
   TinySkiff · Day 26 guided-day prototype
   Behaviours: lightbox explainers (accessible <dialog>), image zoom,
   code language tabs, checkable build steps + progress, scroll-spy rail,
   the hero sounder readout, copy-prompt toast.
   =========================================================================== */

const explainers = {
  esp32: {
    title: "ESP32-S3 board",
    body: "A development board is a friendly package around a tiny computer chip. The ESP32-S3 runs your uploaded sketch, controls pins, reads sensors, and can also use USB, Wi-Fi, and Bluetooth. In this lesson, it sends the ping signal and measures the echo time.",
    shortcut: "Think of it as the project’s brain, not just a USB gadget."
  },
  gpio: {
    title: "GPIO extension board",
    body: "GPIO means general-purpose input/output. These pins are connection points your code can use. The extension board makes them easier to see, reach, and wire without cramming everything onto the ESP32-S3 itself.",
    shortcut: "When a lesson says GPIO 13, look for the pin labelled 13 on the extension board."
  },
  hcsr04: {
    title: "HC-SR04 ultrasonic sensor",
    body: "The HC-SR04 is a distance sensor. One round transducer sends a sound pulse above human hearing, and the other listens for the echo. The board measures the echo time and turns it into distance.",
    shortcut: "Aim the two round transducers straight at a flat target for steadier readings."
  },
  jumpers: {
    title: "Jumper wires",
    body: "Jumper wires make temporary connections without soldering. Female-to-male wires have a socket on one end and a pin on the other, useful when a sensor module and board use different connector styles.",
    shortcut: "If a reading seems impossible, gently reseat the jumper wires before changing code."
  },
  arduino: {
    title: "Arduino IDE",
    body: "Arduino IDE is the desktop app that opens the sketch, compiles it, uploads it to the ESP32-S3, and shows messages from the board in Serial Monitor.",
    shortcut: "Today, the IDE is both your uploader and your measuring display."
  },
  sketch: {
    title: "Official sketch",
    body: "A sketch is the Arduino name for a program. This lesson uses Freenove’s Sketch_19.1_Ultrasonic_Ranging.ino so you can focus first on wiring, observation, and the measurement model.",
    shortcut: "Treat the sketch as a working example to read and modify, not a spell to copy blindly."
  },
  vcc: {
    title: "VCC / 5V",
    body: "VCC is the positive power input for the sensor. In the Freenove circuit, the HC-SR04 is powered from 5V. Power is separate from the signal pins: VCC lets the sensor run; Trig and Echo carry information.",
    shortcut: "Do not swap VCC and GND. That is the first wiring check."
  },
  trig: {
    title: "Trig pin",
    body: "Trig is short for trigger. The ESP32-S3 briefly turns this pin HIGH for about 10 microseconds. That tells the ultrasonic module to start a measurement.",
    shortcut: "Trig is an output — from the board, to the sensor."
  },
  echo: {
    title: "Echo pin",
    body: "Echo is the return signal. The sensor holds Echo HIGH while the sound pulse is making its round trip. Longer HIGH time means the object is farther away.",
    shortcut: "Echo is an input — from the sensor, to the board."
  },
  gnd: {
    title: "Ground / GND",
    body: "Ground is the shared zero-voltage reference. The board and sensor need a common ground so a signal like HIGH or LOW means the same thing to both parts.",
    shortcut: "A missing ground can make everything look haunted. Check it early."
  },
  serial: {
    title: "Serial Monitor",
    body: "Serial Monitor is a text window in Arduino IDE. The board can print messages to it over USB. Here, it prints the measured distance so you can see what the sensor is doing.",
    shortcut: "If the window is blank, check that the baud rate is 115200."
  },
  define: {
    title: "#define",
    body: "#define creates a nickname before the code is compiled. #define trigPin 13 means: whenever the sketch says trigPin, use the number 13. It makes the code easier to read.",
    shortcut: "Nicknames matter because physical pin numbers are easy to forget."
  },
  pulsein: {
    title: "pulseIn()",
    body: "pulseIn() waits for a pin to enter the requested state, then measures how long it stays there. Here it measures how long Echo stays HIGH, which is the sound pulse’s round-trip time.",
    shortcut: "The raw measurement is time. Distance comes after the math."
  },
  divideTwo: {
    title: "Why divide by two?",
    body: "The sound travels from sensor to object, then from object back to sensor. That is two trips. The formula divides by two because you only want the one-way distance to the object.",
    shortcut: "Round trip ÷ 2 = one-way distance."
  },
  wobble: {
    title: "Why readings wobble",
    body: "Real sensors are imperfect. Soft objects absorb sound. Curved or angled objects bounce sound away. Your hand may move. Air temperature slightly changes the speed of sound. A little wobble is normal.",
    shortcut: "Watch the trend: the number should rise as the object moves away and fall as it comes closer."
  },
  flat: {
    title: "Why flat targets help",
    body: "A flat target reflects more sound straight back to the sensor. Round, soft, fuzzy, or angled targets scatter the sound, so the echo can be weaker or inconsistent.",
    shortcut: "Use a book or a wall when testing."
  },
  threshold: {
    title: "Threshold",
    body: "A threshold turns a measurement into a decision. For example: if distance is less than 15 cm, beep. That pattern is the bridge from reading a sensor to building an interactive device.",
    shortcut: "Pick a threshold that would make sense in a real project, not a random number."
  }
};

/* --------------------------------------------------------------------------
   Lightbox explainer dialog
   -------------------------------------------------------------------------- */
const explainerDialog = document.querySelector("#explainer");
const explainerTitle = document.querySelector("#explainerTitle");
const explainerBody = document.querySelector("#explainerBody");
const explainerShortcut = document.querySelector("#explainerShortcut");
let lastTrigger = null;

function openExplainer(trigger) {
  const item = explainers[trigger.dataset.topic];
  if (!item) return;
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
  // move focus to the close button for keyboard users
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
    document.querySelector("#" + t.getAttribute("aria-controls")).hidden = !selected;
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
   Checkable build steps + progress + completion banner
   -------------------------------------------------------------------------- */
const steps = Array.from(document.querySelectorAll(".step"));
const stepBar = document.querySelector("#stepBar");
const stepCount = document.querySelector("#stepCount");
const doneBanner = document.querySelector("#doneBanner");

function refreshSteps() {
  const done = steps.filter((s) => s.classList.contains("done")).length;
  stepBar.style.width = (done / steps.length) * 100 + "%";
  stepCount.textContent = `${done} / ${steps.length} done`;
  doneBanner.classList.toggle("show", done === steps.length);
}

function toggleStep(step) {
  const done = step.classList.toggle("done");
  step.querySelector(".box").setAttribute("aria-pressed", String(done));
  refreshSteps();
}

steps.forEach((step) => {
  // the box button carries the accessible toggle (keyboard + click)
  step.querySelector(".box").addEventListener("click", () => toggleStep(step));
  // clicking the text is a convenience toggle; Define chips stopPropagation
  step.querySelector(".text").addEventListener("click", () => toggleStep(step));
});

/* --------------------------------------------------------------------------
   Scroll-spy rail
   -------------------------------------------------------------------------- */
const railLinks = Array.from(document.querySelectorAll(".rail-nav a"));
const sections = railLinks
  .map((a) => document.querySelector(a.getAttribute("href")))
  .filter(Boolean);

if ("IntersectionObserver" in window) {
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
  sections.forEach((s) => spy.observe(s));
}

/* --------------------------------------------------------------------------
   Hero sounder — live readout (respects reduced motion)
   -------------------------------------------------------------------------- */
const sounderValue = document.querySelector("#sounderValue");
const sounderTarget = document.querySelector("#sounderTarget");
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

if (sounderValue && !reduceMotion) {
  // The target line steps between a few distances; the readout is that
  // distance plus a small, plausible wobble — like a real sensor.
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
    sounderValue.innerHTML = (base + wobble).toFixed(2) + "<small>cm</small>";
  }, 140);
  setInterval(() => {
    i = (i + 1) % targets.length;
    sounderTarget.style.right = targets[i].px + "px";
    base = targets[i].cm;
  }, 2600);
}

/* --------------------------------------------------------------------------
   Copy-prompt → toast
   -------------------------------------------------------------------------- */
const toast = document.querySelector("#toast");
document.querySelectorAll("[data-copy]").forEach((btn) => {
  btn.addEventListener("click", async () => {
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
