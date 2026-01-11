import time
from ui_framework import Page, get_colors
from picovector import HALIGN_LEFT, HALIGN_CENTER, VALIGN_MIDDLE
from wifi_manager import STATE_IDLE, STATE_CONNECTING, STATE_CONNECTED, STATE_FAIL, STATE_AP_MODE

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
