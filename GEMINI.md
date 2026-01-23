# Picore-W Display App

## Project Overview
This project is a feature-rich, modern IoT dashboard application designed for the **Raspberry Pi Pico W** coupled with the **Pimoroni Presto** (480x480 IPS display). It leverages a custom MicroPython UI framework to provide a responsive, page-based user experience with gesture controls and smooth transitions.

**Key Capabilities:**
*   **Modern UI:** Page-based navigation with swipe gestures, smooth animations, and page indicators.
*   **Robust Networking:** Non-blocking, async WiFi management (`wifi_manager.py`) with auto-reconnection and a Captive Portal (AP Mode) for easy provisioning.
*   **Real-time Data:** Live Crypto prices (via Binance WebSocket) and Weather updates (via Open-Meteo).
*   **Persistent Settings:** On-device configuration storage for WiFi credentials and user preferences (`param_store.py`).

## Tech Stack
*   **Hardware:** Raspberry Pi Pico W (RP2040), Pimoroni Presto Display.
*   **Runtime:** MicroPython (Pimoroni flavor with `picovector` and `presto` libraries).
*   **Language:** Python 3 (MicroPython).
*   **Libraries:** `uasyncio` (core concurrency), `picovector` (graphics), `presto` (hardware interface).

## Directory Structure
*   **`src/`**: Contains the main application source code. **This is the deployment payload.**
    *   `main.py`: Application entry point. Initializes hardware, subsystems, and the UI loop.
    *   `ui_framework.py`: Core logic for the `AppManager` and `Page` base class. Handles input and rendering.
    *   `wifi_manager.py`: Async state machine for WiFi connectivity.
    *   `param_store.py`: Singleton for managing and persisting application settings (`app_params.json`).
    *   `config.py`: Static configuration for UI, WiFi, and APIs.
    *   `*Page.py`: Individual screen implementations (e.g., `ClockPage`, `CryptoPage`, `WeatherPage`).
    *   `templates/`: HTML templates for the provisioning web server.
*   **`examples/`**: Collection of standalone scripts demonstrating specific hardware features (LEDs, sensors, simple graphics).
*   **`debugPic/`**: Images used for debugging or documentation.

## Development & Deployment

### Building
There is no "build" step. This is an interpreted MicroPython project.

### Running / Deploying
1.  **Environment:** Ensure your Pico W is flashed with the latest [Pimoroni MicroPython firmware](https://github.com/pimoroni/pimoroni-pico) that includes Presto support.
2.  **Deployment:** Copy the **contents** of the `src/` directory to the root of the Pico W's filesystem.
    *   *Crucial:* Ensure the `templates/` directory is copied as a subdirectory.
    *   *Crucial:* Ensure `Roboto-Medium.af` (font file) is present on the device root (usually found in `examples/` or root).
3.  **Execution:** Reset the device to run `main.py` automatically, or execute `main.py` via an IDE like Thonny.

### Configuration
*   **Static Config:** Edit `src/config.py` for hardcoded constants (colors, API endpoints, timeouts).
*   **Runtime Config:** User settings (TimeZone, Location, Clock Mode) are stored in `param_store.py` and persisted to `app_params.json` on the device.
*   **WiFi Config:** WiFi credentials are stored separately by `wifi_manager.py` (via `config_manager.py`) in `wifi.json`.

## Coding Conventions
*   **Async/Await:** The application relies heavily on `uasyncio`. Avoid blocking code in the main loop or UI callbacks.
*   **UI Architecture:**
    *   New screens must inherit from `Page` (in `ui_framework.py`).
    *   Implement `draw(self, display, vector, offset_x)` for rendering.
    *   Implement `update(self)` for logic.
    *   Register the page in `main.py` using `app_manager.add_page()`.
*   **State Management:** Use `param_store.subscribe()` to react to setting changes (e.g., timezone updates) without polling.

## Hardware & Frozen Modules API
The firmware includes frozen modules for controlling the Presto hardware.

### `presto` Module
*   **`Presto` Class**: Main interface.
    *   `__init__(full_res=False, palette=False, ambient_light=False, ...)`: Init hardware. `full_res=True` for 480x480.
    *   `update()`: Refresh display and poll touch.
    *   `partial_update(x, y, w, h)`: Efficient partial refresh.
    *   `async_connect()`: Async WiFi connection.
    *   `touch_a`, `touch_b`: Access touch points.
*   **`Buzzer` Class**: Control piezo buzzer (`set_tone(freq, duty)`).

### `touch` Module
*   **`FT6236` Class**: Driver for the touch controller.
*   **`Button` Class**: Helper for creating soft buttons (`is_pressed()`).

### `ezwifi` Module
*   **`EzWiFi` Class**: Simplified WiFi management with callbacks (`connected`, `failed`).

### `lsm6ds3` Module
*   **`LSM6DS3` Class**: Accelerometer/Gyro driver (`get_readings()`, `step_count`, gesture detection).

### `psram` Module
*   **`PSRAMBlockDevice`**: For mounting PSRAM as a filesystem.
*   **`mkramfs()`**: Helper to create a RAM filesystem.

### `qwstpad` Module
*   **`QwSTPad` Class**: Driver for external I2C button/LED pads.

## Presto AI Coding Reference

### 1. Basic Setup & Display
**Boilerplate (240x240):**
```python
from presto import Presto
presto = Presto(ambient_light=True)
display = presto.display
WIDTH, HEIGHT = display.get_bounds()

while True:
    display.set_pen(display.create_pen(0, 0, 0)) # Black
    display.clear()
    display.set_pen(display.create_pen(255, 255, 255)) # White
    display.text("Hello AI", 10, 10, WIDTH, 4)
    presto.update()
```
**Full Resolution (480x480):**
```python
# Use palette=True to save RAM
presto = Presto(full_res=True, palette=True)
display = presto.display
```

### 2. Touch Interaction
```python
from presto import Presto
from touch import Button
presto = Presto()
touch = presto.touch
btn_ok = Button(20, 100, 100, 50) # x, y, w, h

while True:
    touch.poll()
    if btn_ok.is_pressed():
        # Action
    presto.update()
```

### 3. Graphics (`PicoVector`)
```python
from picovector import PicoVector, Polygon, Transform, ANTIALIAS_BEST
vector = PicoVector(display)
vector.set_antialiasing(ANTIALIAS_BEST)
t = Transform()
vector.set_transform(t)

tri = Polygon()
tri.path((0, -20), (15, 10), (-15, 10))
t.translate(120, 120)
vector.draw(tri)
```

### 4. WiFi & Networking
**Async Connect:**
```python
await presto.async_connect()
```
**HTTP Get:**
```python
import requests
req = requests.get("http://api.example.com/data.json")
data = req.json()
req.close()
```

### 5. Sensors & LEDs
**Accelerometer (LSM6DS3):**
```python
from lsm6ds3 import LSM6DS3, NORMAL_MODE_104HZ
import machine
sensor = LSM6DS3(machine.I2C(), mode=NORMAL_MODE_104HZ)
ax, ay, az, gx, gy, gz = sensor.get_readings()
```
**RGB LEDs:**
```python
presto.set_led_rgb(0, 255, 0, 0) # Index, R, G, B
```

### 6. Audio
```python
from presto import Buzzer
buzzer = Buzzer(43)
buzzer.set_tone(440) # 440Hz
buzzer.set_tone(-1)  # Off
```

### 7. Storage (SD Card)
```python
import machine, sdcard, uos
sd_spi = machine.SPI(0, sck=machine.Pin(34), mosi=machine.Pin(35), miso=machine.Pin(36))
sd = sdcard.SDCard(sd_spi, machine.Pin(39))
uos.mount(sd, "/sd")
```

## Key Commands (Manual)
Since there is no CLI for deployment, file operations are typically handled via IDEs or tools like `mpremote`.

*   **List files on device:** `mpremote ls`
*   **Copy src to device:** `mpremote cp -r src/* :` (approximate command, depends on tool)
*   **Reset device:** `mpremote reset`
