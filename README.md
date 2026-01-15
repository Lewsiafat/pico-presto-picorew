# Picore-W Display App

A feature-rich display application for **Raspberry Pi Pico W** and **Pimoroni Presto**, built on the robust **Picore-W** network library. This project demonstrates how to create a modern, responsive IoT dashboard with smooth transitions and real-time data fetching.

## Key Features

### 🖥️ Modern UI Framework
- **Page-Based Navigation**: Modular architecture using `AppManager` and `Page` classes.
- **Gesture Control**: Swipe **Left/Right** to navigate between pages.
- **Smooth Transitions**: Slide animations for a premium user experience.
- **Page Indicators**: Visual cues for navigation position.
- **Startup Experience**: Professional boot screen with logo and progress bar.

### 📡 Robust Networking (Picore-W Core)
- **Asynchronous**: Non-blocking WiFi management using `uasyncio`.
- **Auto-Recovery**: Automatically reconnects if the network drops.
- **Smart Provisioning**: Launches a configuration AP if no credentials are found.

### 📊 Built-in Pages
1.  **Startup Page**: Boot animation (3 seconds).
2.  **Status Page**: Real-time Network State, IP Address, and Uptime.
3.  **Crypto Page**: Live Bitcoin (BTC) & Ethereum (ETH) prices (via CoinGecko, updates every 20s).
4.  **Weather Page**: Real-time weather updates (Temp & Condition) for Taipei (via Open-Meteo).

---

## Hardware Requirements
- Raspberry Pi Pico W (RP2040)
- Pimoroni Presto Display (480x480 IPS)

## Installation
1.  **Flash Firmware**: Ensure your Pico W is running the latest Pimoroni MicroPython firmware supporting Presto.
2.  **Upload Code**: Copy all files from the `src/` directory to the **root** of your Pico W.
    - Any subfolders (like `templates/`) must be preserved.
3.  **Run**: Reset the device or run `main.py` in Thonny.

## Configuration
Edit `src/config.py` to customize the application:
- **`UIConfig`**: Colors, Startup Duration, Animations, API URLs.
- **`WiFiConfig`**: Connection timeouts, Retries, AP settings.

## Architecture

| File | Description |
| :--- | :--- |
| `main.py` | Application entry point. Initializes Hardware, WiFi, and UI. |
| `ui_framework.py` | Core UI logic (`AppManager`, `Page`), Input handling, Transitions. |
| `StartupPage.py` | Initial boot screen logic. |
| `StatusPage.py` | Network status display logic. |
| `CryptoPage.py` | Cryptocurrency ticker logic. |
| `WeatherPage.py` | Weather display logic (Open-Meteo). |
| `wifi_manager.py` | Background WiFi state machine. |
| `config.py` | Centralized configuration. |

---

## License
MIT License.
