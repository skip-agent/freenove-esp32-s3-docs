# 30-day curriculum spine

Resolved for: [Choose the 30-day curriculum spine](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/4)  
Map: [Wayfinder Map: TinySkiff ESP32-S3 guided 30-day tutorial spec](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/1)

## Executive answer

Use the official Freenove C/Arduino order, cleaned up into a 30-day core course.

The core course should end with a **TCP/IP mini web-connected device**. Camera, audio, and USB HID should become a separate follow-up course, not squeezed into the 30-day beginner path.

Structure:

- Main path: **Arduino/C++**.
- Course length: **30 core days**.
- Daily format: mission-card — goal → parts → steps → test → challenge → logbook.
- Lesson voice: friendly workshop guide.
- Duplicate/paired official projects: **merge into one day** and use variants as the challenge.
- MicroPython: optional side-path only when it helps the same concept.
- Advanced follow-up: camera, SD/audio, USB HID, and deeper network/device projects.

## Curriculum principles

1. **Preserve official order.** Learners should be able to cross-reference the Freenove PDFs and sketches without hunting through a rearranged course.
2. **Clean up the pacing.** Closely related projects become one day with one small challenge, rather than separate dense days.
3. **Avoid front-loading setup.** Install drivers/Arduino setup first, then install libraries just-in-time.
4. **Keep every day ≤30 minutes.** Advanced examples are scoped as “make the official example run, then change one tiny thing,” or moved to the follow-up course.
5. **End with a working network mental model.** The core course should finish with Wi-Fi/TCP because that is the cleanest beginner-friendly bridge from electronics into internet-connected devices.
6. **Keep camera/audio/USB out of the core.** They are exciting but likely to become long troubleshooting sessions. They deserve a follow-up course with more breathing room.

## Core 30-day course

| Day | Mission | Official source basis | Challenge style |
|---:|---|---|---|
| 1 | Unbox safely and meet the ESP32-S3 | `Start Here.pdf`, `README.md`, `Super.jpg`, `ESP32S3_Pinout.png` | Identify three parts and mark the board’s USB/data path in the logbook. |
| 2 | Install Arduino IDE, CH343 driver if needed, and confirm the board appears | CH343 docs, Arduino configuration images | Change one setting back and forth, then restore the correct board/port choice. |
| 3 | Blink: prove computer → cable → board → code → LED | `Sketch_01.1_Blink`; C Tutorial Chapter 0/1 Blink material | Change blink timing and name the pattern. |
| 4 | Button + LED: make input control output | `Sketch_02.1_ButtonAndLed` | Predict the LED state before pressing the button, then test. |
| 5 | Mini table lamp: turn the button project into a tiny product | `Sketch_02.2_TableLamp` | Change the lamp behavior: toggle speed, hold behavior, or label the interaction. |
| 6 | LED bar: make motion with multiple outputs | `Sketch_03.1_FlowingLight` | Reverse the flow direction. |
| 7 | PWM: fade an LED instead of just switching it | `Sketch_04.1_BreathingLight` | Find a fade speed that feels calm. |
| 8 | Meteor light: reuse PWM thinking across several LEDs | `Sketch_04.2_FlowingLight2` | Change the trail length or speed. |
| 9 | RGB LED: mix color from code | `Sketch_05.1_RandomColorLight`, `Sketch_05.2_GradientColorLight` | Pick a “status color” and write down its RGB values. |
| 10 | Buzzer: make the board speak in beeps | `Sketch_06.1_Doorbell`, `Sketch_06.2_Alertor` | Invent a two-beep signal and describe what it means. |
| 11 | Serial monitor: see what the board is saying | `Sketch_07.1_SerialPrinter` | Change the printed message and upload again. |
| 12 | Serial read/write: send instructions back to the board | `Sketch_07.2_SerialRW` | Add or test one extra command/response. |
| 13 | Potentiometer / ADC: read a changing voltage | `Sketch_08.1_ADC` | Turn the knob slowly and record the lowest/highest values seen. |
| 14 | Touch sensor: use your body as an input | `Sketch_09.1_TouchRead`, `Sketch_09.2_TouchLamp` | Pick a threshold and explain why it works. |
| 15 | Soft light: map analog input to LED brightness | `Sketch_10.1_SoftLight` | Make the LED respond more gently or more sharply. |
| 16 | Soft colorful light: map analog input to color | `Sketch_10.2_SoftColorfulLight` | Create a named color mood from the knob. |
| 17 | Night lamp: respond to ambient light | `Sketch_11.1_NightLamp` | Find the point where the lamp should turn on in your room. |
| 18 | Thermometer: sense temperature | `Sketch_12.1_Thermometer` | Warm the sensor gently with your hand and describe the change. |
| 19 | Joystick: read two axes and a button | `Sketch_13.1_Joystick` | Predict which number changes before opening Serial Monitor. |
| 20 | Shift register LED bar: control many outputs with fewer pins | `Sketch_14.1_FlowingLight02` | Change the pattern from flowing to bouncing or filling. |
| 21 | Seven-segment display: show one digit clearly | `Sketch_15.1_1_Digit_7-Segment_Display` | Display a favorite digit and explain which segments light up. |
| 22 | Motor driver: control motion safely | `Sketch_16.1_Control_Motor_by_L293D` | Change speed carefully and record the quietest reliable speed. |
| 23 | Servo sweep: move to positions, not just spin | `Sketch_17.1_Servo_Sweep` | Limit the sweep range and explain why smaller movement can be useful. |
| 24 | Servo knob: control position with a potentiometer | `Sketch_17.2_Control_Servo_by_Potentiometer` | Make a tiny “gauge” and label min/mid/max. |
| 25 | LCD1602: give the project a display | `Sketch_18.1_Display_the_string_on_LCD1602` | Show a custom two-line message. |
| 26 | Ultrasonic distance: measure the world | `Sketch_19.1_Ultrasonic_Ranging`, `Sketch_19.2_Ultrasonic_Ranging` | Measure three objects and compare the readings. |
| 27 | BLE pass-through: talk wirelessly at short range | `Sketch_20.1_BLE_USART` | Send one custom message over BLE and log what worked. |
| 28 | Bluetooth control LED: wireless command → physical output | `Sketch_20.2_BluetoothToLed` | Rename or change one command/action pair. |
| 29 | Wi-Fi modes: join a network and understand AP vs station | `Sketch_23.1_WiFi_Station`, `Sketch_23.2_WiFi_AP`, `Sketch_23.3_AP_Station` | Draw which device is the “host” and which is the “guest” for each mode. |
| 30 | TCP/IP mini web-connected device | `Sketch_24.1_WiFiClient`, `Sketch_24.2_WiFiServer` | Change one response/message and visit it from another device if possible. |

## Why these merges work

The official material has more runnable sketches than a 30-day beginner path can hold. The course should merge related official projects when they teach the same mental model:

- Blink variants become one early confidence day.
- Button + table lamp become two days because the interaction model changes from direct input to product-like behavior.
- Random RGB and gradient RGB become one day because both teach color mixing.
- Doorbell and alertor become one buzzer day because both teach sound feedback.
- Touch read and touch lamp become one day because the sensor and application are tightly coupled.
- Ultrasonic variants become one day unless the second variant is needed for display integration.
- Wi-Fi station/AP/AP+station become one conceptual day before TCP/IP.
- TCP client/server become the final core day because it is the natural endpoint of “internet-connected device” basics.

## Follow-up course boundary

The following official chapters should **not** be squeezed into the 30-day core course. They are valuable, but they are too troubleshooting-heavy or multi-concept for the beginner course’s 30-minute daily rhythm.

Follow-up course candidates:

| Follow-up area | Official source basis | Why it moves out of core |
|---|---|---|
| SD card read/write | `Sketch_21.1_SDMMC_Test` | Storage wiring/card formatting can derail a short beginner day. |
| Audio from SD | `Sketch_22.1_PlayMP3FromSD` | Combines SD card, audio library, speaker/amplifier behavior, and file prep. |
| Camera web server | `Sketch_25.1_CameraWebServer`, `Sketch_25.2_As_VideoWebServer`, `Sketch_25.3_Camera_SDcard` | Needs privacy notes, network troubleshooting, and more image/server context. |
| Camera TCP server | `Sketch_26.1_CameraTcpServer` | Builds on networking plus camera behavior; better after camera basics. |
| USB serial/HID | `Sketch_27.1_USBSerial` through `Sketch_27.4_ConsumerControl` | USB mode/host behavior is powerful but easy to confuse with normal upload/debug USB. |
| Deeper MicroPython track | `Python/Python_Codes/` | Useful alternate path, but not required for Arduino-first mastery. |

The 30-day spec can include a short “Where to go next” panel that points to these follow-up weeks, but should not promise production-ready follow-up lessons in this map.

## Image and asset implications

The curriculum spine makes the image map sharper:

- Days 1–2 need direct assets already present: `Super.jpg`, `ESP32S3_Pinout.png`, `Arduino_Configuration_USB_OTG.png`, and `Arduino_Configuration_USB_UART.png`.
- Days 3–30 need circuit diagrams and wiring screenshots extracted or mapped from `C/C_Tutorial.pdf`.
- Follow-up camera/audio/USB assets should be deferred until the follow-up course exists.
- Every lesson should record source PDF/page, extracted asset path, alt text, and attribution.

## Hardware-risk notes for future drafting

These days are likely to need extra inline safety/debug notes:

- Day 2: CH343, board/port, USB data cable.
- Day 9: RGB LED pin orientation.
- Day 10: buzzer polarity and volume expectations.
- Days 20–21: shift register wiring density.
- Days 22–24: motor/servo movement and external power expectations.
- Day 25: LCD I2C address/library setup.
- Day 26: ultrasonic sensor wiring and reading stability.
- Days 27–30: phone/BLE/network credentials and local network assumptions.

## Implications for the remaining Wayfinder map

- [Prototype one guided day](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/5) should use a mid-course representative day, preferably Day 14 Touch Lamp or Day 26 Ultrasonic Distance, because those show wiring, sensing, debugging, and a small challenge without the complexity of networking.
- [Specify the site content model and navigation](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/6) should model `course: core-30` separately from future `course: follow-up-advanced` so camera/audio/USB can be added later without bloating the first release.
- [Assemble the ready-to-implement tutorial spec](https://github.com/skip-agent/freenove-esp32-s3-docs/issues/7) should include the follow-up boundary as an explicit non-goal for the first implementation phase.

No new ticket is required now. The follow-up advanced course should become a separate future map only after the 30-day core spec is complete.
