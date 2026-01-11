import time
import uasyncio as asyncio
import urequests
from ui_framework import Page, get_colors
from picovector import HALIGN_LEFT, HALIGN_CENTER, VALIGN_MIDDLE
from config import UIConfig

class CryptoPage(Page):
    def __init__(self, app_manager):
        super().__init__("Crypto", app_manager)
        self.colors = get_colors(app_manager.display)
        self.prices = {"bitcoin": 0, "ethereum": 0}
        self.last_fetch_time = 0
        self.fetch_interval = UIConfig.CRYPTO_REFRESH_INTERVAL
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
            url = UIConfig.CRYPTO_API_URL
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
