# DRAFT — "Board not showing up" troubleshooting for TSK-DAY02-SETUP

Status: proposal, not published. Do not treat as live content.
Author: lesson-improvement helper run, 2026-07-11.
Target lesson: `lessons/day-02-setup.yml` (TSK-DAY02-SETUP).
Trigger: a live learner hit "ESP32-S3 does not appear in Arduino IDE; board is
plugged in and a blue LED is flashing on it."

---

## What Day 2 already covers (and covers well)

- **Charge-only vs data cable** — fully covered. Steps item (line 69), the
  `usbData` glossary entry, and the check "Board lights up, but no port?"
  (line 124) all point at swapping in a data-capable cable.
- **Board vs port selection** — covered in steps (lines 70–71) and the check
  "Board name missing from the list?" (line 126).
- **The CH343 driver exists and why** — covered conceptually by `usbSerial`
  (line 738), `usbDriver`, the steps fallback (line 72), and the check "No port
  appears at all?" (line 122).

## The three gaps that match this learner's symptom

A blinking LED means power is reaching the board and it is running code, so the
cable is delivering power and the port has power. The break is somewhere in the
**data path**. Day 2 does not currently walk a beginner through the three data-path
causes that most often produce exactly this "lit up but no port" state:

1. **Two USB-C ports (biggest gap).** The Freenove ESP32-S3-WROOM in this kit has
   **two** USB-C ports, not one. One is wired to the CH343 USB-to-serial chip
   (the UART/COM port); the other is the ESP32-S3's own native USB. With the
   default Arduino setup, only the CH343 port makes a serial port appear. Plug
   into the native-USB port and the board still lights up and still runs its
   demo — but no port shows up in Arduino IDE. Day 1 line 81 and Day 2 both say
   "the USB-C port" (singular), so a learner has no reason to suspect they picked
   the wrong one. This is the single most likely cause of the reported symptom.
   (Confirmed against the Freenove board repo, which ships two separate configs,
   `Arduino_Configuration_USB_UART.png` and `Arduino_Configuration_USB_OTG.png`.)

2. **No per-OS driver-install detail, and no macOS "Allow" step.** Day 2 links
   the CH343 download but never says what installing it looks like on each OS —
   and on modern macOS the installer is blocked until you approve it in
   **System Settings → Privacy & Security**, which stops many beginners cold.

3. **Manual download mode is in the glossary but never surfaced here.** The exact
   recovery — **hold BOOT, tap RESET, release BOOT** — lives in `autoReset`
   (line 748) and `bootReset` (line 680), but neither is referenced from Day 2
   and it is not in the troubleshooting checks. When a previous or crashing
   sketch stops the board enumerating, forcing download mode by hand is the step
   that makes it appear.

---

## Where this slots in

Two edits, both in `lessons/day-02-setup.yml`:

- **A.** Replace the current `test.checks` list (lines 121–127) with the expanded
  list below. It keeps the existing three checks and adds the wrong-port, driver
  per-OS, and manual-download-mode checks, ordered cheapest-first.
- **B.** Add the two supporting glossary keys (`twoPorts`, `manualBoot`) to
  `lessons/_glossary.yml`, and reference `{twoPorts}` from the Day 1 board-tour
  step and the Day 2 plug-in step so the two-port fact is taught before it bites.

A one-word fix in Day 1 (line 81) also helps: change "Find the USB-C port along
one edge" to name that there may be two and only one talks to Arduino IDE.

After editing YAML, run the semantic refresh per root `AGENTS.md`, rebuild the
course pages, and re-run `scripts/tests/test_course.py` (the `checks` shape test
requires each item to keep `symptom` + `fix`).

---

## A. Proposed `test.checks` replacement (ready to paste)

```yaml
  checksTitle: If it doesn't
  checks:
    - symptom: "Board lit up or a light blinking, but no port appears?"
      fix: "Good news first- a light means power is reaching the board, so your cable and the port both work. The missing piece is the *data* path. Work down the next four checks in order; most 'lit up but no port' cases are the first one."
    - symptom: "Two USB-C ports on the board?"
      fix: "This kit's board has two. Only one is wired to the CH343 chip that Arduino IDE talks to; the other is the chip's own USB and stays invisible with the default setup. Move your cable to the *other* USB-C port, then unplug and replug while watching Tools → Port. Use whichever port makes an entry appear and disappear- that's the CH343 (UART/COM) port. Leave the cable there for the rest of the course."
    - symptom: "Still no port after trying both ports and a known data cable?"
      fix: "Install the [CH343 driver](https://github.com/Freenove/Freenove_Super_Starter_Kit_for_ESP32_S3/tree/main/CH343) for your system, then replug. **Windows:** run the `.exe`, let it finish, replug- the board shows up as `COM4`, `COM5`, and so on. **macOS:** open the `.pkg`, then go to **System Settings → Privacy & Security** and click **Allow** for the WCH/CH34x system software (it waits there until you do), restart if it asks, then replug- the board shows up as `/dev/cu.wchusbserial…`. **Linux:** the driver is usually already built in; if the port never appears, add yourself to the `dialout` group (`sudo usermod -aG dialout $USER`), log out and back in, then replug- it shows up as `/dev/ttyACM0` or `/dev/ttyUSB0`. (Some other boards use a CH340 or CP2102 chip instead; the idea is the same, just a different driver.)"
    - symptom: "Port appears but uploads fail, or the board seems stuck?"
      fix: "Put the board into download mode by hand: **hold BOOT, tap RESET once, then release BOOT.** That tells the board to listen for new code instead of running the program that's crashing. Select the port and upload straight after. Once your sketch is on, the board resets and runs on its own- you only do this when the automatic handshake can't."
    - symptom: "Board name missing from the list?"
      fix: "Confirm **esp32 by Espressif Systems** is installed in Boards Manager. Then choose **Select other board and port…** and select **ESP32S3 Dev Module**."
```

Note on ordering: the first item is a reassurance-plus-routing check written to
match the learner's exact words ("lit up but no port"), pointing them down the
list. If you would rather not add a non-actionable check (it still carries a
concrete `fix`, so it passes the schema), fold its wording into the intro of
`test.checksTitle` instead and start the list at the two-ports check.

---

## B. Proposed glossary additions (`lessons/_glossary.yml`)

```yaml
twoPorts:
  title: Two USB-C ports
  body: >
    This board has two USB-C ports, and they do different jobs. One is wired to
    the CH343 chip that turns the board's serial into USB — that is the port
    Arduino IDE sees, and the one you upload through. The other is the ESP32-S3's
    own built-in USB, used for special modes later on. Both deliver power and
    both light the board up, so a lit board on the wrong port looks identical to
    a working one — except no port shows up. When in doubt, unplug and replug
    while watching Tools → Port and use whichever port makes an entry appear.
  shortcut: Two USB-C ports- upload through the CH343 one (the one that makes a port appear).

manualBoot:
  title: Download mode by hand
  body: >
    To receive new code, the board must be in download mode at the moment the
    upload starts. The IDE normally flips it there for you, but some cables and
    hubs break that handshake, and a crashing sketch can stop the board
    responding at all. You can force it yourself- hold BOOT, tap RESET once, let
    RESET go, then release BOOT. The board is now waiting for code. Upload, and
    when it finishes the board resets and runs your program on its own.
  shortcut: Hold BOOT, tap RESET, release BOOT- forces the board to listen for a new upload.
```

Then reference them from the steps:

- Day 1, board tour (line 81), change to:
  `Find the USB-C port along one edge — some boards have two, and only the one wired to the serial chip talks to Arduino IDE. Power and code both arrive here. {twoPorts}`
- Day 2, plug-in step (line 69), append `{twoPorts}` alongside `{usbData}`.
- Day 2, theory `notes` or a new note referencing `{manualBoot}` so the manual
  procedure is taught once, then pointed to from the check.

---

## Voice check

Written to match the course: teach-by-doing, plain beginner language, concrete
"do this, watch that happen" instructions, no quiz or reflection questions, no
filler, no "not X, it's Y" phrasing, no use of "quiet." The reassurance about the
blinking LED is framed as a positive fact (power works, so look at the data path)
rather than by negation.
