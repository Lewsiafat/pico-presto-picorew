import time
import urequests
import uasyncio as asyncio
from ui_framework import Page, get_colors
from picovector import HALIGN_LEFT, HALIGN_CENTER, VALIGN_MIDDLE, HALIGN_RIGHT
from config import UIConfig, WeatherConfig

class WeatherPage(Page):
    def __init__(self, app_manager):
        super().__init__("Weather", app_manager)
        self.colors = get_colors(app_manager.display)
        
        self.temp = 0.0
        self.wmo_code = -1
        self.is_day = 1
        self.last_fetch_time = 0
        self.fetch_interval = WeatherConfig.UPDATE_INTERVAL
        self.last_error = None
        
        self.weather_map = {
            0: "Clear Sky",
            1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
            45: "Fog", 48: "Rime Fog",
            51: "Drizzle", 53: "Drizzle", 55: "Drizzle",
            61: "Rain", 63: "Rain", 65: "Heavy Rain",
            71: "Snow", 73: "Snow", 75: "Heavy Snow",
            80: "Rain Showers", 81: "Rain Showers", 82: "Violent Rain",
            95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm"
        }

    async def enter(self):
        super().enter()
        # Trigger fetch if data is stale or never fetched
        if time.time() - self.last_fetch_time > self.fetch_interval or self.last_fetch_time == 0:
            await self.fetch_weather()

    async def update(self):
        # Periodic fetch
        if time.time() - self.last_fetch_time > self.fetch_interval:
            await self.fetch_weather()

    async def fetch_weather(self):
        print("WeatherPage: Fetching data...")
        self.last_error = None
        try:
            # Construct URL for Open-Meteo
            url = f"{WeatherConfig.API_URL}?latitude={WeatherConfig.LATITUDE}&longitude={WeatherConfig.LONGITUDE}&current_weather=true"
            
            headers = {'User-Agent': 'PicoreW/1.0'}
            res = urequests.get(url, headers=headers)
            
            if res.status_code != 200:
                self.last_error = f"HTTP {res.status_code}"
                res.close()
                return

            data = res.json()
            res.close()
            
            current = data.get("current_weather", {})
            self.temp = current.get("temperature", 0.0)
            self.wmo_code = current.get("weathercode", 0)
            self.is_day = current.get("is_day", 1)
            
            self.last_fetch_time = time.time()
            print(f"WeatherPage: Updated Temp={self.temp}, Code={self.wmo_code}")
            
        except Exception as e:
            self.last_error = str(e)
            print(f"WeatherPage: Fetch failed: {e}")

    def get_weather_desc(self, code):
        return self.weather_map.get(code, "Unknown")

    def draw_error(self, display, vector, message, width, height, offset_x):
        display.set_pen(self.colors["RED"])
        vector.set_font_size(18)
        vector.set_font_align(HALIGN_CENTER | VALIGN_MIDDLE)
        vector.text(message, (width // 2) + offset_x, int(height * 0.5))

    def draw(self, display, vector, offset_x=0):
        width, height = display.get_bounds()
        
        # Header
        header_y = int(height * 0.12)
        vector.set_font_size(26)
        vector.set_font_align(HALIGN_LEFT | VALIGN_MIDDLE)
        display.set_pen(self.colors["WHITE"])
        vector.text("Weather", int(width * 0.1) + offset_x, header_y)

        if self.last_error:
            self.draw_error(display, vector, f"Error: {self.last_error}", width, height, offset_x)
            return

        if self.last_fetch_time == 0:
            self.draw_error(display, vector, "Loading Data...", width, height, offset_x)
            return

        # Main Temperature Display
        temp_y = int(height * 0.45)
        vector.set_font_size(80)
        vector.set_font_align(HALIGN_CENTER | VALIGN_MIDDLE)
        
        # Color based on temp
        if self.temp >= 30:
            display.set_pen(self.colors["ORANGE"])
        elif self.temp <= 15:
            display.set_pen(self.colors["CYAN"])
        else:
            display.set_pen(self.colors["GREEN"])
            
        vector.text(f"{self.temp:.1f}°C", (width // 2) + offset_x, temp_y)

        # Condition Text
        cond_y = int(height * 0.65)
        condition_text = self.get_weather_desc(self.wmo_code)
        
        vector.set_font_size(24)
        display.set_pen(self.colors["WHITE"])
        vector.text(condition_text, (width // 2) + offset_x, cond_y)

        # Footer
        footer_y = int(height * 0.85)
        vector.set_font_size(16)
        vector.set_font_align(HALIGN_CENTER | VALIGN_MIDDLE)
        display.set_pen(self.colors["GRAY"])
        vector.text("Loc: Taipei", (width // 2) + offset_x, footer_y)
