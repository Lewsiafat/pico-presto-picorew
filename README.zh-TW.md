# Picore-W Display App

專為 **Raspberry Pi Pico W** 和 **Pimoroni Presto** 設計的功能豐富顯示應用程式，建立在強大的 **Picore-W** 網路連線庫之上。本專案展示了如何構建一個具有流暢轉場效果與即時數據更新的現代化物聯網儀表板。

## 主要功能

### 🖥️ 現代化 UI 架構
- **頁面式導航 (Page-Based)**：使用 `AppManager` 與 `Page` 類別的模組化架構。
- **手勢控制**：支援 **左/右** 滑動手勢切換頁面。
- **流暢轉場**：如同智慧型手機般的滑動動畫效果。
- **頁面指示器**：底部顯示當前頁面位置的小圓點。
- **開機體驗**：專業的 Logo 開機畫面與讀取進度條。

### 📡 強韌的網路核心 (Picore-W)
- **非同步設計**：使用 `uasyncio` 進行非阻塞式的 WiFi 管理。
- **自動修復**：網路斷線時自動重新連線。
- **智慧配網**：若無儲存的網路設定，自動開啟 AP 模式供使用者設定。

### 📊 內建頁面
1.  **Startup Page (啟動頁)**：開機動畫展示 (3 秒)。
2.  **Status Page (狀態頁)**：即時顯示網路連線狀態、IP 地址與系統運行時間。
3.  **Crypto Page (加密貨幣頁)**：顯示比特幣 (BTC) 與乙太幣 (ETH) 即時價格 (來源 CoinGecko，每 60 秒更新)。

---

## 硬體需求
- Raspberry Pi Pico W (RP2040)
- Pimoroni Presto Display (480x480 IPS)

## 安裝方式
1.  **燒錄韌體**：確保您的 Pico W 運行支援 Presto 的最新 Pimoroni MicroPython 韌體。
2.  **上傳程式碼**：將 `src/` 目錄下的所有檔案複製到 Pico W 的 **根目錄**。
    - 請務必包含 `templates/` 等子資料夾。
3.  **執行**：重新啟動裝置，或在 Thonny 中執行 `main.py`。

## 設定 (Configuration)
編輯 `src/config.py` 以自定義應用程式：
- **`UIConfig`**：設定顏色、啟動時間、動畫速度、API 網址等。
- **`WiFiConfig`**：設定連線逾時、重試次數、AP 模式參數。

## 專案架構

| 檔案 | 描述 |
| :--- | :--- |
| `main.py` | 應用程式進入點。初始化硬體、WiFi 與 UI。 |
| `ui_framework.py` | 核心 UI 邏輯 (`AppManager`, `Page`)、輸入處理、轉場特效。 |
| `StartupPage.py` | 開機畫面的邏輯。 |
| `StatusPage.py` | 網路狀態顯示頁面的邏輯。 |
| `CryptoPage.py` | 加密貨幣價格顯示頁面的邏輯。 |
| `wifi_manager.py` | 負責背景運行的 WiFi 狀態機。 |
| `config.py` | 集中式設定檔。 |

---

## 授權 (License)
MIT License.