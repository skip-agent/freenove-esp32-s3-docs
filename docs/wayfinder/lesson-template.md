# Lesson voice and repeatable day template

Resolved for: [Define the lesson voice and repeatable day template](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/3)  
Map: [Wayfinder Map: ESP32-S3 guided 30-day tutorial spec](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/1)

## Executive answer

Every daily lesson should read like a **friendly workshop guide**: warm, clear, and lightly playful, but not cutesy. The learner is an adult beginner: curious and capable, with no electronics assumed.

Use a repeatable **mission-card** format:

> goal → parts → steps → test → challenge → logbook

Each day should feel like a small, complete win. The main path should stay practical and uncluttered. Explanations should appear inline as short **“why this works”** notes, not as long theory sections. Safety and troubleshooting should appear **inline only when relevant**, not as a repeated daily box.

## Voice

Use this voice:

- Friendly workshop guide.
- Warm, clear, lightly playful.
- Practical and confidence-building.
- Adult-beginner language; no condescension.
- Fun through discovery and small wins, not forced jokes.

Avoid:

- Long textbook exposition before the learner touches the kit.
- Overly childish “STEM camp” tone.
- Dense datasheet language in the main lesson.
- Treating rewritten Freenove prose as a copyedit exercise. Rewrite for the learner.

Good voice pattern:

> Today you’ll make the ESP32-S3 blink an LED on purpose. It sounds tiny, but it proves the whole toolchain works: computer → USB cable → board → code → physical output.

Bad voice pattern:

> In this experiment, we will learn how to control the output level of GPIO pin by program.

## Daily lesson template

Each day uses the same top-level sections.

### 1. Goal

One short paragraph that says what the learner will make and why it matters.

Include:

- The visible outcome.
- The concept unlocked.
- The expected time, capped at 30 minutes.

Example:

> **Goal:** Make one LED blink from your own code. You’ll prove that Arduino IDE can talk to the ESP32-S3 and that GPIO pins can control the physical world. Time: about 20 minutes.

### 2. Parts

A short checklist of only the parts needed today.

Include:

- Board.
- Breadboard/wires/resistors/components.
- Any library/software needed today.
- Official image/diagram if available.

Rules:

- Do not list the whole kit every day.
- Do not install all libraries up front. Install just-in-time.
- Mention orientation-sensitive parts when relevant.

### 3. Steps

The main guided build.

Use short, numbered steps. Each step should do one thing.

Preferred rhythm:

1. Wire or prepare one small thing.
2. Check it before powering or uploading.
3. Open the matching official sketch.
4. Upload/run it.
5. Observe the result.

Rules:

- Put wiring before code when the circuit matters.
- Put “power off before rewiring” inline only on days where rewiring risk is real.
- Use screenshots/diagrams near the exact step where they help.
- Keep code explanation local to the code being changed.

### 4. Test

A quick proof that the day worked.

Each test should answer:

- What should I see/hear/measure?
- How do I know the board is doing the right thing?
- What is the fastest fix if it does not work?

Example:

> **Test:** The LED should turn on and off once per second. If nothing happens, check that the right board and port are selected, then try a different USB data cable.

### 5. Challenge

A tiny extension, always doable inside the 30-minute total day.

Challenge style should rotate:

- Tiny modification to the official project.
- Observation challenge: measure, notice, explain.
- Creative twist: make it personal/fun.

Rules:

- One challenge per day.
- The challenge should not require new parts unless the day already introduced them.
- The challenge should preserve the learner’s working baseline: change one thing, then test.
- Advanced days may use a smaller challenge, e.g. “change one setting and observe the result.”

Examples:

- Change the blink speed and write down which delay feels like a heartbeat.
- Make the RGB LED show your “status color.”
- Move the joystick and predict which value changes before you read the serial monitor.

### 6. Logbook

End each day with a tiny reflection.

Purpose:

- Reinforce the concept.
- Give the learner a visible sense of progress.
- Surface troubleshooting notes for the next day.

Format:

- “What did you make?”
- “What surprised you?”
- “What would you change next?”

Keep it optional but visible.

## Inline notes

### “Why this works” notes

Use short inline notes when a concept matters right now.

Good scope:

- 2–4 sentences.
- Tied to the step the learner just performed.
- Explains the useful mental model, not the entire theory.

Example:

> **Why this works:** A GPIO pin is a tiny switch the program can control. When the pin goes HIGH, voltage appears at the pin. The resistor keeps the LED current in a safe range.

Avoid:

- Multi-paragraph theory blocks.
- Datasheet references in the main path unless the day is explicitly about pinouts/specs.
- “Go deeper” sections that become a second lesson.

### Safety and troubleshooting notes

Safety and debugging appear inline only when relevant.

Use callouts for:

- Rewiring while powered.
- Polarity/orientation-sensitive parts.
- Motor/servo movement.
- Short-circuit risk.
- CH343/USB/port/upload failures.
- Library installation failures.
- Wi-Fi credentials or camera privacy.

Do not add a generic safety box to every lesson.

Recommended callout labels:

- **Check before power** — wiring or short-circuit risk.
- **If upload fails** — board/port/cable/driver fixes.
- **Careful: moving parts** — motor/servo days.
- **Privacy note** — camera/network days.

## Main path vs optional material

Main lesson includes:

- Today’s goal.
- Needed parts.
- Official circuit/image/code references.
- Guided build steps.
- Minimal code explanation.
- Relevant safety/troubleshooting.
- One challenge.
- Logbook prompt.

Optional material appears inline as short **“why this works”** notes.

Do not create large separate theory sections in the first version. If a concept cannot fit into a short inline note, it should become either:

- a later day,
- a glossary/reference page, or
- a future optional side quest.

MicroPython belongs in optional side-path material only when it helps the same day’s concept. It should not interrupt the Arduino-first main path.

## Acceptance rules for future lesson drafts

A lesson draft passes this template when:

- It can be completed by an adult beginner in 30 minutes or less.
- It starts with a concrete thing the learner will make.
- It lists only today’s parts and software needs.
- It has numbered, action-first steps.
- It uses official images/diagrams where helpful and gives alt text.
- It includes only relevant safety/troubleshooting callouts.
- It has exactly one small challenge.
- It ends with a logbook prompt.
- It keeps explanations short and inline.
- It preserves Freenove attribution and non-affiliation language where source material is reused.

## Implications for the remaining Wayfinder map

- [Choose the 30-day curriculum spine](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/4) should express every day in this mission-card rhythm.
- [Prototype one guided day](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/5) should use this exact template, including one inline “why this works” note and one relevant troubleshooting callout if needed.
- [Specify the site content model and navigation](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/6) should model the six required lesson sections directly rather than treating lessons as freeform Markdown blobs.

No new tickets are required from this resolution.
