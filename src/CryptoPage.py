import time
import uasyncio as asyncio
import json
from simple_websocket import WebSocket
from ui_framework import Page, get_colors
from picovector import HALIGN_LEFT, HALIGN_CENTER, HALIGN_RIGHT, VALIGN_MIDDLE
from config import UIConfig

class CryptoPage(Page):
    def __init__(self, app_manager):
        super().__init__("Crypto", app_manager)
        self.colors = get_colors(app_manager.display)
        self.prices = {"bitcoin": 0.0, "ethereum": 0.0}
        
        # Flash state: {symbol: {'color': color_code, 'time': start_ticks}}
        self.flash_state = {} 
        self.FLASH_DURATION = 500 # ms
        
        self.ws_task = None
        self.ws_client = None
        self.last_error = None
        self.is_connected = False

    def enter(self):
        super().enter()
        self.last_error = None
        # Defers WS connection to update() to prevent freezing the transition


    def exit(self):
        super().exit()
        if self.ws_task:
            self.ws_task.cancel()
            self.ws_task = None
        if self.ws_client:
            self.ws_client.close()
            self.ws_client = None
        self.is_connected = False

    async def update(self):
        # Start WS task here, after transition is complete (UI_STATE_NORMAL)
        if self.ws_task is None:
            self.ws_task = asyncio.create_task(self.params_ws_loop()) 

    async def params_ws_loop(self):
        while True:
            try:
                print("CryptoPage: Connecting to Binance WS...")
                self.is_connected = False
                
                self.ws_client = WebSocket(UIConfig.CRYPTO_WS_URL)
                await self.ws_client.connect()
                
                self.is_connected = True
                self.last_error = None 
                print("CryptoPage: Connected!")

                while True:
                    msg = await self.ws_client.recv()
                    if msg:
                        self.process_message(msg)
                    else:
                        print("CryptoPage: WS closed")
                        break
            except asyncio.CancelledError:
                print("CryptoPage: WS Task Cancelled")
                if self.ws_client:
                    self.ws_client.close()
                return
            except Exception as e:
                self.last_error = f"{str(e)}"
                self.is_connected = False
                print(f"CryptoPage: WS Error: {e}")
                if self.ws_client:
                    self.ws_client.close()
                await asyncio.sleep(5) 

    def process_message(self, msg):
        try:
            data = json.loads(msg)
            if not isinstance(data, dict):
                return
            
            stream_data = data.get("data", {})
            symbol = stream_data.get("s")
            price_str = stream_data.get("p")
            
            if symbol and price_str:
                price = float(price_str)
                key = "bitcoin" if "BTC" in symbol else "ethereum"
                
                old_price = self.prices.get(key, 0.0)
                self.prices[key] = price
                
                if old_price > 0:
                    if price > old_price:
                        self.flash_state[key] = {'color': self.colors["GREEN"], 'time': time.ticks_ms()}
                    elif price < old_price:
                        self.flash_state[key] = {'color': self.colors["RED"], 'time': time.ticks_ms()}
                        
        except Exception as e:
            print(f"CryptoPage: Parse error: {e}")

    def draw_label_value(self, display, vector, label, value, y_pos, base_color, width, height, offset_x, flash_key=None):
        label_x = int(width * 0.1) + offset_x
        # Revert to Left Align at 35% width to ensure visibility
        value_x = int(width * 0.35) + offset_x
        
        # Check flash
        display_color = base_color
        if flash_key and flash_key in self.flash_state:
            state = self.flash_state[flash_key]
            if time.ticks_diff(time.ticks_ms(), state['time']) < self.FLASH_DURATION:
                display_color = state['color']
            else:
                del self.flash_state[flash_key]
        
        vector.set_font_size(18)
        vector.set_font_align(HALIGN_LEFT | VALIGN_MIDDLE)
        display.set_pen(self.colors["GRAY"])
        vector.text(label, label_x, y_pos)
        
        vector.set_font_size(24)
        # Revert to Left Align
        vector.set_font_align(HALIGN_LEFT | VALIGN_MIDDLE)
        display.set_pen(display_color)
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
            self.draw_error(display, vector, f"{self.last_error}", width, height, offset_x)
            if btc_price == 0: return 
        
        if not self.is_connected and btc_price == 0 and not self.last_error:
             self.draw_error(display, vector, "Connecting...", width, height, offset_x)
             return

        row1_y = int(height * 0.35)
        row2_y = int(height * 0.50)
        
        self.draw_label_value(display, vector, "BTC:", f"${btc_price:,.2f}", row1_y, self.colors["YELLOW"], width, height, offset_x, "bitcoin")
        self.draw_label_value(display, vector, "ETH:", f"${eth_price:,.2f}", row2_y, self.colors["CYAN"], width, height, offset_x, "ethereum")

        # Footer
        footer_y = int(height * 0.85)
        vector.set_font_size(16)
        vector.set_font_align(HALIGN_CENTER | VALIGN_MIDDLE)
        display.set_pen(self.colors["GRAY"])
        status = "Binance Live" if self.is_connected else "Reconnecting..."
        vector.text(status, (width // 2) + offset_x, footer_y)
