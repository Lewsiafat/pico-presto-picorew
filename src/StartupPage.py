import time
from ui_framework import Page, get_colors
from picovector import HALIGN_LEFT, VALIGN_MIDDLE
from config import UIConfig

class StartupPage(Page):
    def __init__(self, app_manager):
        super().__init__("Startup", app_manager)
        self.colors = get_colors(app_manager.display)
        self.start_time = 0
        self.duration = UIConfig.STARTUP_DURATION
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
