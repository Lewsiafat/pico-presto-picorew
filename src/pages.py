import time
import uasyncio as asyncio
import urequests
from picovector import HALIGN_CENTER, HALIGN_LEFT, VALIGN_MIDDLE
from ui_framework import Page
from wifi_manager import STATE_IDLE, STATE_CONNECTING, STATE_CONNECTED, STATE_FAIL, STATE_AP_MODE

# Colors
def get_colors(display):
    return {
        "BLACK": display.create_pen(0, 0, 0),
        "WHITE": display.create_pen(255, 255, 255),
        "GRAY": display.create_pen(50, 50, 50),
        "GREEN": display.create_pen(0, 255, 0),
        "RED": display.create_pen(255, 50, 50),
        "ORANGE": display.create_pen(255, 165, 0),
        "BLUE": display.create_pen(50, 150, 255),
        "YELLOW": display.create_pen(255, 215, 0),
        "CYAN": display.create_pen(0, 255, 255)
    }

class StatusPage(Page):
    def __init__(self, app_manager):
        super().__init__("Status", app_manager)
        self.colors = get_colors(app_manager.display)
        self.wm = app_manager.wm
        
        self.status_map = {
            STATE_IDLE: ("IDLE", self.colors["GRAY"]),
            STATE_CONNECTING: ("CONNECTING", self.colors["ORANGE"]),
            STATE_CONNECTED: ("CONNECTED", self.colors["GREEN"]),
            STATE_FAIL: ("FAILED", self.colors["RED"]),
            STATE_AP_MODE: ("AP MODE", self.colors["BLUE"]),
        }

    def draw_label_value(self, display, vector, label, value, y_pos, value_color, width, height, offset_x):
        # Apply offset_x
        label_x = int(width * 0.1) + offset_x
        value_x = int(width * 0.4) + offset_x
        
        vector.set_font_size(18)
        vector.set_font_align(HALIGN_LEFT | VALIGN_MIDDLE)
        display.set_pen(self.colors["GRAY"])
        vector.text(label, label_x, y_pos)
        
        vector.set_font_size(24)
        vector.set_font_align(HALIGN_LEFT | VALIGN_MIDDLE)
        display.set_pen(value_color)
        vector.text(str(value), value_x, y_pos)

    def draw(self, display, vector, offset_x=0):
        width, height = display.get_bounds()
        
        # Layout
        header_y = int(height * 0.12)
        row1_y = int(height * 0.35)
        row2_y = int(height * 0.50)
        divider_y = int(height * 0.65)
        footer_y = int(height * 0.85)

        # Header
        vector.set_font_size(26)
        vector.set_font_align(HALIGN_LEFT | VALIGN_MIDDLE)
        display.set_pen(self.colors["WHITE"])
        vector.text("Network Status", int(width * 0.1) + offset_x, header_y)

        # Status
        status_code = self.wm.get_status()
        status_text, status_color = self.status_map.get(status_code, ("UNKNOWN", self.colors["GRAY"]))
        self.draw_label_value(display, vector, "Status:", status_text, row1_y, status_color, width, height, offset_x)

        # IP
        config = self.wm.get_config()
        ip = config[0] if config else "0.0.0.0"
        self.draw_label_value(display, vector, "IP:", ip if ip != "0.0.0.0" else "---", row2_y, self.colors["WHITE"], width, height, offset_x)

        # Divider
        display.set_pen(self.colors["GRAY"])
        margin = int(width * 0.1)
        display.rectangle(margin + offset_x, divider_y, width - (margin * 2), 2)

        # Footer
        vector.set_font_size(16)
        vector.set_font_align(HALIGN_CENTER | VALIGN_MIDDLE)
        display.set_pen(self.colors["GRAY"])
        vector.text(f"Uptime: {time.ticks_ms() // 1000}s", (width // 2) + offset_x, footer_y)


class CryptoPage(Page):
    def __init__(self, app_manager):
        super().__init__("Crypto", app_manager)
        self.colors = get_colors(app_manager.display)
        self.prices = {"bitcoin": 0, "ethereum": 0}
        self.last_fetch_time = 0
        self.fetch_interval = 60
        self.last_error = None

    async def enter(self):
        super().enter()
        # Trigger fetch if needed when entering the page
        if time.time() - self.last_fetch_time > self.fetch_interval:
            await self.fetch_prices()

    async def update(self):
        # Periodic fetch
        if time.time() - self.last_fetch_time > self.fetch_interval:
            await self.fetch_prices()

    async def fetch_prices(self):
        print("CryptoPage: Fetching prices...")
        self.last_error = None
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
            headers = {'User-Agent': 'PicoreW/1.0'}
            
            res = urequests.get(url, headers=headers)
            if res.status_code != 200:
                self.last_error = f"HTTP {res.status_code}"
                res.close()
                return

            data = res.json()
            res.close()
            
            self.prices["bitcoin"] = data.get("bitcoin", {}).get("usd", 0)
            self.prices["ethereum"] = data.get("ethereum", {}).get("usd", 0)
            self.last_fetch_time = time.time()
            print(f"CryptoPage: Prices updated: {self.prices}")
        except Exception as e:
            self.last_error = str(e)
            print(f"CryptoPage: Fetch failed: {e}")

    def draw_label_value(self, display, vector, label, value, y_pos, value_color, width, height, offset_x):
        label_x = int(width * 0.1) + offset_x
        value_x = int(width * 0.4) + offset_x
        
        vector.set_font_size(18)
        vector.set_font_align(HALIGN_LEFT | VALIGN_MIDDLE)
        display.set_pen(self.colors["GRAY"])
        vector.text(label, label_x, y_pos)
        
        vector.set_font_size(24)
        vector.set_font_align(HALIGN_LEFT | VALIGN_MIDDLE)
        display.set_pen(value_color)
        vector.text(str(value), value_x, y_pos)

    def draw_error(self, display, vector, message, width, height, offset_x):
        display.set_pen(self.colors["RED"])
        vector.set_font_size(18)
        vector.set_font_align(HALIGN_CENTER | VALIGN_MIDDLE)
        if len(message) > 20:
             parts = [message[i:i+20] for i in range(0, len(message), 20)]
             y = int(height * 0.5)
             for i, part in enumerate(parts):
                 vector.text(part, (width // 2) + offset_x, y + (i * 20))
        else:
             vector.text(message, (width // 2) + offset_x, int(height * 0.5))

    def draw(self, display, vector, offset_x=0):
        width, height = display.get_bounds()
        
        # Header
        header_y = int(height * 0.12)
        vector.set_font_size(26)
        vector.set_font_align(HALIGN_LEFT | VALIGN_MIDDLE)
        display.set_pen(self.colors["WHITE"])
        vector.text("Crypto Prices", int(width * 0.1) + offset_x, header_y)

        btc_price = self.prices.get("bitcoin", 0)
        eth_price = self.prices.get("ethereum", 0)

        if self.last_error:
            self.draw_error(display, vector, f"Error: {self.last_error}", width, height, offset_x)
        elif btc_price == 0:
            self.draw_error(display, vector, "Loading Data...", width, height, offset_x)
        else:
            row1_y = int(height * 0.35)
            row2_y = int(height * 0.50)
            self.draw_label_value(display, vector, "BTC:", f"${btc_price:,}", row1_y, self.colors["YELLOW"], width, height, offset_x)
            self.draw_label_value(display, vector, "ETH:", f"${eth_price:,}", row2_y, self.colors["CYAN"], width, height, offset_x)

        # Footer
        footer_y = int(height * 0.85)
        vector.set_font_size(16)
        vector.set_font_align(HALIGN_CENTER | VALIGN_MIDDLE)
        display.set_pen(self.colors["GRAY"])
        vector.text("Updates every 60s", (width // 2) + offset_x, footer_y)

class StartupPage(Page):
    def __init__(self, app_manager):
        super().__init__("Startup", app_manager)
        self.colors = get_colors(app_manager.display)
        self.start_time = 0
        self.duration = 3000 # 3 seconds
        self.switched = False

    def enter(self):
        super().enter()
        self.start_time = time.ticks_ms()
        self.switched = False

    async def update(self):
        # Check timer
        if not self.switched and time.ticks_diff(time.ticks_ms(), self.start_time) > self.duration:
            # Auto-advance to the next page (usually StatusPage at index 1)
            self.switched = True
            self.app.switch_page(1)

    def draw(self, display, vector, offset_x=0):
        width, height = display.get_bounds()
        
        # Explicitly set alignment to CENTER for logo
        # Using manual centering calculation to be robust against alignment flag issues
        
        # Logo Text
        vector.set_font_size(36)
        # Reset alignment to Left to use manual calc (safest)
        vector.set_font_align(HALIGN_LEFT | VALIGN_MIDDLE)
        display.set_pen(self.colors["WHITE"])
        
        text1 = "Pimoroni"
        # measure_text returns (x, y, w, h)
        _, _, w1, _ = vector.measure_text(text1)
        x1 = int((width - w1) // 2) + offset_x
        vector.text(text1, x1, height // 2 - 20)
        
        # Subtitle
        vector.set_font_size(28)
        text2 = "Presto"
        _, _, w2, _ = vector.measure_text(text2)
        x2 = int((width - w2) // 2) + offset_x
        
        display.set_pen(self.colors["BLUE"])
        vector.text(text2, x2, height // 2 + 20)
        
        # Loading bar
        display.set_pen(self.colors["GRAY"])
        bar_width = 200
        progress = min(1.0, time.ticks_diff(time.ticks_ms(), self.start_time) / self.duration)
        
        display.rectangle((width//2 - bar_width//2) + offset_x, height - 60, bar_width, 4)
        display.set_pen(self.colors["GREEN"])
        display.rectangle((width//2 - bar_width//2) + offset_x, height - 60, int(bar_width * progress), 4)
