# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Picore-W Display App 是一個為 **Raspberry Pi Pico W** 和 **Pimoroni Presto** (480x480 IPS 顯示器) 設計的 MicroPython IoT 儀表板應用程式。

## Development & Deployment

這是 MicroPython 專案，沒有傳統的建置或測試指令。

**部署流程：**
1. 將 `src/` 目錄下的所有檔案上傳至 Pico W 的根目錄
2. 保持 `templates/` 子目錄結構
3. 透過 Thonny 執行 `main.py` 或重啟裝置

**韌體需求：**
- Pimoroni MicroPython 韌體 (支援 Presto)
- 需要 `Roboto-Medium.af` 向量字型檔案

## Architecture

### Core Components

**UI Framework (`ui_framework.py`)**
- `Page` - 所有頁面的抽象基底類別，定義生命週期方法：`enter()`, `exit()`, `update()`, `draw()`, `on_tap()`
- `AppManager` - 管理頁面導航、觸控輸入、滑動過場動畫
- UI 狀態常數：`UI_STATE_NORMAL`, `UI_STATE_SLIDE_LEFT`, `UI_STATE_SLIDE_RIGHT`

**WiFi Manager (`wifi_manager.py`)**
- 非同步狀態機處理 WiFi 連線生命週期
- 狀態定義於 `constants.py`: `STATE_IDLE`, `STATE_CONNECTING`, `STATE_CONNECTED`, `STATE_FAIL`, `STATE_AP_MODE`
- 無憑證時自動進入 AP 模式提供 Web 介面配置

**Parameter Store (`param_store.py`)**
- 單例模式參數管理器，透過 `get_params()` 取得實例
- 支援 Observer Pattern 實現雙向綁定：`subscribe(key, callback)`, `unsubscribe(key, callback)`
- 自動持久化至 `app_params.json`
- 預設參數：`timezone_offset`, `weather_latitude`, `weather_longitude`, `weather_interval`, `clock_mode`

**頁面系統**
- 每個頁面繼承 `Page` 類別
- 頁面透過 `app_manager.add_page()` 註冊
- 索引 0 (StartupPage) 禁用滑動手勢，會自動跳轉

### Key Patterns

**建立新頁面：**
```python
from ui_framework import Page, get_colors

class MyPage(Page):
    def __init__(self, app_manager):
        super().__init__("PageName", app_manager)
        self.colors = get_colors(app_manager.display)

    def enter(self):
        super().enter()
        # 頁面啟動時執行

    def draw(self, display, vector, offset_x=0):
        # 繪製 UI，offset_x 用於滑動過場
```

**設定配置：**
- `config.py` 集中管理 `UIConfig`, `WiFiConfig`, `WeatherConfig`
- 顏色定義使用 RGB tuple 於 `UIConfig.COLOR_PALETTE`

**非同步資料獲取：**
- 使用 `uasyncio` 進行非阻塞網路操作
- WebSocket 連線範例見 `CryptoPage.py` (Binance 即時行情)
- HTTP API 範例見 `WeatherPage.py` (Open-Meteo)

### File Dependencies

```
main.py
  └── ui_framework.py (AppManager, Page)
  └── param_store.py (參數管理與持久化)
  └── wifi_manager.py
        └── config_manager.py (憑證持久化)
        └── dns_server.py (AP 模式 captive portal)
        └── web_server.py (配置頁面)
        └── constants.py (狀態常數)
        └── config.py
  └── Pages
        └── ClockPage.py (使用 param_store 取得 timezone_offset, clock_mode)
        └── WeatherPage.py (使用 param_store 取得 weather_latitude, weather_longitude, weather_interval)
        └── SettingsPage.py (設定頁面，修改所有參數)
```

## External APIs

- **Binance WebSocket**: `wss://stream.binance.com:9443/stream` - 即時加密貨幣價格
- **Open-Meteo**: `https://api.open-meteo.com/v1/forecast` - 天氣資料
- **NTP**: 連線成功後自動同步時間
