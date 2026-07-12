# Source inventory for ESP32-S3 guided tutorial

Resolved for: [Inventory source docs, examples, and reusable images](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/2)  
Map: [Wayfinder Map: ESP32-S3 guided 30-day tutorial spec](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/1)

## Executive answer

The repo has enough official material to specify a 30-day, Arduino-first guided course without inventing the electronics sequence from scratch.

Use the official C/Arduino tutorial as the curriculum backbone. It has 27 chapters and 45 sketches, covering the full kit from blink through USB/camera/SD/audio. Treat MicroPython as optional side-quests: it has 36 projects and good beginner feedback loops, but less complete advanced coverage.

The main implementation gap is not content availability; it is extraction and curation. The converted Markdown has usable text but no embedded images. Most useful diagrams live inside the PDFs and must be extracted or manually mapped per lesson. The current static site already indexes code and copies only a small set of top-level images.

## Source package

Official source archive recorded in `source-manifest/freenove-source.json`:

- Source: <https://github.com/Freenove/Freenove_Super_Starter_Kit_for_ESP32_S3/archive/refs/heads/main.zip>
- Local archive: `archives/freenove-super-starter-kit-esp32-s3-main.zip`
- SHA-256: `22f4e57030d8fad343bd032033c0942e7ab04ff6d06a16cb074b6fc277c06e53`
- Downloaded: `2026-07-08T20:08:53Z`
- Archive size: 218,589,916 bytes
- Entries: 704

Unpacked source root:

`source/Freenove_Super_Starter_Kit_for_ESP32_S3-main/`

Top-level source areas:

- `Start Here.pdf` — short onboarding, chip-removal safety, common problems.
- `README.md` — official GitHub front door, product images, license summary.
- `C/C_Tutorial.pdf` — main Arduino/C++ tutorial, 324 pages after conversion markers.
- `C/Sketches/` — 45 Arduino sketches.
- `C/Libraries/` — 12 zipped Arduino libraries.
- `Python/Python_Tutorial.pdf` — MicroPython tutorial, 260 pages after conversion markers.
- `Python/Python_Codes/` — 36 MicroPython projects.
- `Python/Python_Libraries/` — 14 helper libraries.
- `Python/Python_Firmware/` and `Python/Python_Software/` — Thonny/firmware setup assets.
- `CH343/` — USB serial driver packages and notes.
- `Datasheet/` — 21 component/board/camera datasheet PDFs.

Converted Markdown currently present:

- `converted/start-here.md` — 3,055 chars, 88 lines; no image markdown.
- `converted/c-tutorial.md` — 280,947 chars, 15,587 lines; no image markdown.
- `converted/python-tutorial.md` — 218,660 chars, 10,979 lines; no image markdown.

Current generated site data:

- `docs/data.json` indexes the examples, libraries, PDFs, source links, and code previews.
- `docs/index.html` embeds the same site data and loads `docs/app.js`.
- `scripts/build_site.py` collects source material and copies selected assets into `docs/`.

## Arduino/C++ coverage: main path

Use this as the primary 30-day course spine.

The C/Arduino source has 45 sketches:

| Area | Source coverage | Curriculum use |
|---|---|---|
| Setup / board basics | README, Start Here, CH343, Arduino configuration, GPIO notes | Days 1–2 setup and safety |
| LED basics | Blink, ButtonAndLed, TableLamp, FlowingLight | First confidence wins |
| PWM / analog / color | BreathingLight, FlowingLight2, RGB random/gradient, ADC | Core control concepts |
| Sound | Doorbell, Alertor | Fun quick feedback |
| Serial | SerialPrinter, SerialRW | Debugging and communication mental model |
| Touch / potentiometer / LDR / thermistor | TouchRead, TouchLamp, SoftLight, NightLamp, Thermometer | “Make the board sense the world” arc |
| Joystick and shift register | Joystick, 74HC595 LED bar, 7-segment display | Inputs + output expansion |
| Motion | L293D motor, servo sweep, servo controlled by potentiometer | Mechanical output; needs safety notes |
| Display | LCD1602 | First “device-like” UI |
| Distance | Ultrasonic ranging projects | Sensor-to-display/challenge material |
| Wireless | BLE USART, BluetoothToLed, Wi-Fi station/AP/AP+station, TCP client/server | Advanced connectivity arc |
| Storage/audio/camera/USB | SDMMC, MP3 from SD, camera web/video/TCP, USB serial/mouse/keypad/consumer control | Capstone or optional advanced days |

Important Arduino libraries:

- `DHT_sensor_library_for_ESPx-1.19.zip`
- `ESP32-audioI2S-2.0.0.zip`
- `ESP32Servo-3.0.4.zip`
- `ESP8266Audio-1.9.8.zip`
- `Freenove_IR_Lib_for_ESP32_v1.0.1.zip`
- `Freenove_WS2812_Lib_for_ESP32-2.0.0.zip`
- `IRremoteESP8266-2.8.6.zip`
- `Keypad-3.1.1.zip`
- `LiquidCrystal-1.0.7.zip`
- `LiquidCrystal_I2C-1.1.2.zip`
- `MPU6050_tockn-1.5.2.zip`
- `UltrasonicSensor-1.1.0.zip`

## MicroPython coverage: optional path

Use MicroPython as optional “try it another way” material, not the main path.

The Python source has 36 projects. It largely mirrors beginner-to-intermediate Arduino lessons:

- Hello world, boot, blink.
- Button + LED, table lamp.
- LED bar, breathing LED, RGB.
- Buzzer projects.
- Serial print/read-write.
- Analog read, soft LED, night lamp.
- Thermometer, joystick.
- 74HC595 and 7-segment display.
- Motor, servo, LCD1602, ultrasonic.
- BLE, Wi-Fi station/AP/AP+STA, TCP client/server.
- Camera web server.

Good optional side-quest pattern:

> “If you want a faster code loop today, here is the MicroPython version. Same circuit, different language.”

Do not promise full parity. The C path has SD card, audio, more camera variants, and USB HID examples that are not matched 1:1 in Python. The official `Start Here.pdf` also says Python lacks audio/Bluetooth/video transmission, but the current Python folder does include BLE and a camera web server, so the source statement is stale or imprecise.

Python helper libraries available:

`I2C_LCD.py`, `LCD_API.py`, `adc.py`, `ble_advertising.py`, `dht.py`, `hcsr04.py`, `irrecvdata.py`, `keypad.py`, `mpu6050.py`, `my74HC595.py`, `myservo.py`, `neopixel.py`, `pwm.py`, `stepmotor.py`.

## Reusable images and diagrams

### Direct image files already in source

These are straightforward to reuse and cite:

| Path | Size | Likely use |
|---|---:|---|
| `source/.../Super.jpg` | 1500×1500 | Hero/product overview; kit inventory/opening lesson |
| `source/.../ESP32S3_Pinout.png` | 1694×779 | Persistent pinout reference; setup; every wiring-heavy lesson |
| `source/.../Arduino_Configuration_USB_OTG.png` | 487×672 | Arduino board/USB mode setup |
| `source/.../Arduino_Configuration_USB_UART.png` | 487×694 | Arduino board/USB mode setup |
| `source/.../C/Sketches/Sketch_27.1_USBSerial/configuration.png` | 487×694 | USB serial advanced day |
| `source/.../C/Sketches/Sketch_27.2_MouseControl/configuration.png` | 487×694 | USB mouse/HID advanced day |
| `source/.../C/Sketches/Sketch_27.3_KeyboardControl/configuration.png` | 487×694 | USB keyboard/HID advanced day |
| `source/.../C/Sketches/Sketch_27.4_ConsumerControl/configuration.png` | 487×694 | USB consumer-control advanced day |
| `source/.../CH343/Linux/Linux.png` | 1438×594 | Linux driver setup/troubleshooting appendix |

Current generated copies:

- `docs/assets/Super.jpg`
- `docs/assets/ESP32S3_Pinout.png`
- `docs/assets/Arduino_Configuration_USB_OTG.png`
- `docs/assets/Arduino_Configuration_USB_UART.png`

### Images embedded in PDFs

The converted Markdown did not preserve embedded diagrams. The PDFs contain many embedded images:

- `Start Here.pdf` — 15 image rows via `pdfimages -list`.
- `C/C_Tutorial.pdf` — 785 image rows via `pdfimages -list`.
- `Python/Python_Tutorial.pdf` — 630 image rows via `pdfimages -list`.

Implication for implementation: a later build ticket should extract or screenshot page-specific circuit diagrams from the PDFs, then create an explicit asset manifest such as:

```json
{
  "day": 4,
  "sourcePdf": "C/C_Tutorial.pdf",
  "sourcePage": 46,
  "asset": "assets/lessons/day-04-button-led-circuit.png",
  "alt": "Button connected to ESP32-S3 input pin and LED output circuit"
}
```

The spec should require alt text and attribution for every reused official image.

## Setup gotchas the guided tutorial must smooth out

1. **USB serial driver / CH343 setup**
   - The source spends real space on CH343 driver detection and installation.
   - Beginner flow should include “do you see a serial port?” before asking the learner to upload code.

2. **Correct Arduino board, port, and USB mode**
   - Upload failures are common enough that `Start Here.pdf` calls them out.
   - Existing configuration images should be used in the setup lesson.

3. **USB cable quality**
   - Source troubleshooting says to try another USB cable if the board is not recognized.
   - The guided setup should explicitly say: use a data-capable USB cable, not charge-only.

4. **Remove chips/modules from the breadboard before use**
   - `Start Here.pdf` warns that some chips/modules ship inserted into the breadboard only to protect pins.
   - Preserve this as a photo-backed “unpack safely” step.

5. **GPIO caution**
   - The C and Python tutorials both contain GPIO notes.
   - Guided lessons should include a reusable “pin sanity check” pattern: power off before rewiring; verify 3.3 V vs 5 V expectations; avoid moving wires while powered.

6. **Library installation**
   - Arduino libraries are zipped under `C/Libraries/` and are needed later.
   - The course should not front-load all libraries. Install them just-in-time on the relevant day.

7. **MicroPython firmware and helper libraries**
   - Python path requires Thonny setup, firmware flashing, and uploading helper `.py` libraries.
   - Since MicroPython is optional, keep this in a side path instead of blocking the main course.

8. **Advanced lessons may exceed 30 minutes if treated literally**
   - Camera, SD/audio, USB HID, and Wi-Fi/TCP are likely too big for one beginner sitting unless scoped as “make the official example run, then one tiny modification.”

## Grammar and clarity problems to rewrite

Representative source issues found during inventory:

- `Auther` in code headers should be “Author”.
- `Project doesn’t wok` should be “Project doesn’t work”.
- `Servo Knop` should be “Servo Knob”.
- `Single Chip Micyoco(SCM)` is likely meant to describe a single-chip microcontroller / MCU.
- `Comparing to C, Python doesn’t have...` should become a clear capability comparison.
- `Meet problems? Don't panic!` should become a friendly troubleshooting section.
- `package damage, quality problems, or questions encountered in use` should be rewritten in natural support language.
- `After the downloading completes... an shortcut...` should be rewritten as normal setup copy.
- The existing tutorial often explains component theory, circuit, and code in long blocks. The guided site should chunk each day into action-first steps, quick checks, and short explanations.

Rewrite principle:

> Preserve the official technical facts and images; rewrite the prose as friendly adult-beginner instructions, not as a lightly edited PDF transcription.

## Licensing and attribution constraints

The official README says all repository files are released under Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported.

Implications:

- The tutorial may reuse and adapt the official materials only in a non-commercial context unless separate permission exists.
- Attribution to Freenove should remain visible on the site.
- Adapted/reworked lesson material should preserve the compatible share-alike posture.
- Freenove brand/logo should not be presented as if the site is official. The current “Not affiliated with Freenove” framing should remain.
- Do not remove support links; instead place them in a helpful “When to contact Freenove” section.

Suggested attribution block for the future site:

> This guide is an unofficial learning companion for the Freenove Super Starter Kit for ESP32-S3. It is based on Freenove’s official documentation, examples, images, and source files, licensed under CC BY-NC-SA 3.0. Freenove is a trademark of Freenove Creative Technology Co., Ltd. This site is not affiliated with or endorsed by Freenove.

## Implications for the remaining Wayfinder map

The source inventory makes two later questions sharper:

1. **Curriculum spine:** The 30-day course can be built from the C/Arduino chapter order, but it should compress/merge early redundant lessons and treat camera/audio/USB as scoped capstone or optional advanced days.
2. **Asset plan:** A later implementation spec must include PDF image extraction/mapping. Keeping only the current `docs/assets/*` files is not enough for a truly guided tutorial.

No current ticket is out of scope. No new ticket is required yet; the existing curriculum, prototype, and content-model tickets can absorb the sharpened decisions.
