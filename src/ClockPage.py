import time
import math
from ui_framework import Page, get_colors
from picovector import HALIGN_CENTER, VALIGN_MIDDLE, HALIGN_RIGHT, HALIGN_LEFT

class ClockPage(Page):
    def __init__(self, app_manager):
        super().__init__("Clock", app_manager)
        self.colors = get_colors(app_manager.display)
        self.dim_white = app_manager.display.create_pen(170, 170, 170)
        self.mode = 0 # 0=Digital, 1=Analog
        
    def on_tap(self):
        self.mode = 1 - self.mode # Toggle 0 <-> 1
        print(f"ClockPage: Mode switched to {'Analog' if self.mode == 1 else 'Digital'}")

    def draw(self, display, vector, offset_x=0):
        # Get Time
        # Timezone offset: Taipei is UTC+8. 
        # ntptime sets UTC. We need to add 8 hours (8 * 3600 seconds)
        # Note: This is a simple offset. For robust Timezone support, dedicated libs are better.
        utc_time = time.time()
        local_time = time.localtime(utc_time + (8 * 3600))
        
        if self.mode == 0:
            self.draw_digital(display, vector, local_time, offset_x)
        else:
            self.draw_analog(display, vector, local_time, offset_x)

    def draw_digital(self, display, vector, t, offset_x):
        width, height = display.get_bounds()
        
        # Format: HH:MM:SS
        hh = t[3]
        mm = t[4]
        ss = t[5]
        date_str = f"{t[0]}-{t[1]:02d}-{t[2]:02d}"
        
        # Main Time (HH:MM)
        time_str = f"{hh:02d}:{mm:02d}"
        
        # Layout
        time_y = int(height * 0.45)
        sec_y = int(height * 0.70)
        date_y = int(height * 0.2)
        
        # Date
        vector.set_font_size(24)
        vector.set_font_align(HALIGN_CENTER | VALIGN_MIDDLE)
        display.set_pen(self.colors["GRAY"])
        vector.text(date_str, (width // 2) + offset_x, date_y)

        # Draw HH:MM
        vector.set_font_size(55)
        vector.set_font_align(HALIGN_CENTER | VALIGN_MIDDLE)
        display.set_pen(self.dim_white)
        vector.text(time_str, ((width // 2)-30) + offset_x, time_y)
        
        # Draw Seconds
        # Blinking colon effect or similar? NO, user asked for tick effect.
        # Just drawing the seconds number clearly.
        vector.set_font_size(40)
        display.set_pen(self.colors["ORANGE"])
        vector.text(f":{ss:02d}", (width // 2) + offset_x, sec_y)

    def draw_analog(self, display, vector, t, offset_x):
        width, height = display.get_bounds()
        center_x = (width // 2) + offset_x
        center_y = int(height * 0.5)-10
        radius = int(min(width, height) * 0.4)
        
        # Face
        display.set_pen(self.dim_white)
        display.circle(center_x, center_y, radius)
        display.set_pen(self.colors["BLACK"])
        display.circle(center_x, center_y, radius - 4)
        
        # Update Ticks (12 hours)
        display.set_pen(self.colors["GRAY"])
        for i in range(12):
            angle = math.radians(i * 30)
            x1 = center_x + int(math.sin(angle) * (radius - 20))
            y1 = center_y - int(math.cos(angle) * (radius - 20))
            x2 = center_x + int(math.sin(angle) * (radius - 5))
            y2 = center_y - int(math.cos(angle) * (radius - 5))
            display.line(x1, y1, x2, y2)

        # Hands
        hh = t[3] % 12
        mm = t[4]
        ss = t[5]
        
        # Hour Hand
        h_angle = math.radians((hh * 30) + (mm * 0.5))
        hx = center_x + int(math.sin(h_angle) * (radius * 0.5))
        hy = center_y - int(math.cos(h_angle) * (radius * 0.5))
        display.set_pen(self.colors["WHITE"])
        # Draw thick line (simulated by multiple lines or vector polygon if available)
        # Using simple line for now, maybe 2px offset if possible?
        display.line(center_x, center_y, hx, hy)
        
        # Minute Hand
        m_angle = math.radians(mm * 6)
        mx = center_x + int(math.sin(m_angle) * (radius * 0.75))
        my = center_y - int(math.cos(m_angle) * (radius * 0.75))
        display.set_pen(self.colors["CYAN"])
        display.line(center_x, center_y, mx, my)
        
        # Second Hand
        s_angle = math.radians(ss * 6)
        sx = center_x + int(math.sin(s_angle) * (radius * 0.85))
        sy = center_y - int(math.cos(s_angle) * (radius * 0.85))
        display.set_pen(self.colors["ORANGE"])
        display.line(center_x, center_y, sx, sy)
        
        # Center Hub
        display.set_pen(self.colors["WHITE"])
        display.circle(center_x, center_y, 4)
