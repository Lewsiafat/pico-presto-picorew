import time
import machine
from ui_framework import Page, get_colors
from picovector import HALIGN_LEFT, HALIGN_CENTER, VALIGN_MIDDLE
from wifi_manager import STATE_IDLE, STATE_CONNECTING, STATE_CONNECTED, STATE_FAIL, STATE_AP_MODE
from config_manager import ConfigManager
from config import WiFiConfig

# Confirmation timeout in milliseconds
CONFIRM_TIMEOUT_MS = 3000

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
        
        # Button state
        self.button_bounds = None  # (x, y, w, h) - set during draw
        self.confirm_pending = False
        self.confirm_start_time = 0

    def draw_label_value(self, display, vector, label, value, y_pos, value_color, width, height, offset_x):
        # Apply offset_x
        label_x = int(width * 0.1) + offset_x
        value_x = int(width * 0.4) + offset_x
        
        vector.set_font_size(14)
        vector.set_font_align(HALIGN_LEFT | VALIGN_MIDDLE)
        display.set_pen(self.colors["GRAY"])
        vector.text(label, label_x, y_pos)
        
        vector.set_font_size(18)
        vector.set_font_align(HALIGN_LEFT | VALIGN_MIDDLE)
        display.set_pen(value_color)
        vector.text(str(value), value_x, y_pos)

    def draw_button(self, display, vector, text, center_x, center_y, w, h, bg_color, text_color):
        """Draw a button centered at (center_x, center_y) and store its bounds for tap detection."""
        # Calculate top-left corner from center
        x = center_x - w // 2
        y = center_y - h // 2
        # todo this should be cal with btn width 
        btn_text_width = len(text) * 12
        btn_text_height = 12
        # Draw button background
        display.set_pen(bg_color)
        display.rectangle(x, y, w, h)
        
        # Draw button text centered
        vector.set_font_size(12)
        vector.set_font_align(HALIGN_CENTER | VALIGN_MIDDLE)
        display.set_pen(text_color)
        vector.text(text, center_x - round(btn_text_width/3.7), center_y + round(btn_text_height/3))
        
        # Store bounds for tap detection
        self.button_bounds = (x, y, w, h)

    def on_tap(self):
        """Handle tap events - check if button was tapped."""
        if self.button_bounds is None:
            return
        
        # Get touch position from app manager
        touch = self.app.touch
        touch_x = touch.x
        touch_y = touch.y
        
        bx, by, bw, bh = self.button_bounds
        
        # Check if tap is within button bounds
        if bx <= touch_x <= bx + bw and by <= touch_y <= by + bh:
            if self.confirm_pending:
                # Second tap - confirm and reset
                print("StatusPage: Confirmed! Resetting to AP Mode...")
                self._reset_to_ap_mode()
            else:
                # First tap - enter confirmation mode
                print("StatusPage: Tap again to confirm reset")
                self.confirm_pending = True
                self.confirm_start_time = time.ticks_ms()
        else:
            # Tapped outside button - cancel confirmation
            self.confirm_pending = False

    def _reset_to_ap_mode(self):
        """Delete WiFi config and reboot to enter AP mode."""
        print("StatusPage: Deleting WiFi config and rebooting...")
        ConfigManager.delete_config()
        # Brief delay to ensure config is deleted
        time.sleep(0.5)
        machine.reset()

    def draw(self, display, vector, offset_x=0):
        width, height = display.get_bounds()
        
        # Check confirmation timeout
        if self.confirm_pending:
            if time.ticks_diff(time.ticks_ms(), self.confirm_start_time) > CONFIRM_TIMEOUT_MS:
                self.confirm_pending = False
        
        # Get status to determine layout
        status_code = self.wm.get_status()
        status_text, status_color = self.status_map.get(status_code, ("UNKNOWN", self.colors["GRAY"]))
        is_ap_mode = (status_code == STATE_AP_MODE)
        
        # Layout - adjust for AP mode (more rows needed)
        header_y = int(height * 0.10)
        if is_ap_mode:
            row1_y = int(height * 0.24)
            row2_y = int(height * 0.36)
            row3_y = int(height * 0.48)  # SSID row
            row4_y = int(height * 0.60)  # Password row
            divider_y = int(height * 0.70)
            button_y = int(height * 0.80)
        else:
            row1_y = int(height * 0.32)
            row2_y = int(height * 0.45)
            divider_y = int(height * 0.55)
            button_y = int(height * 0.68)

        # Header
        vector.set_font_size(26)
        vector.set_font_align(HALIGN_LEFT | VALIGN_MIDDLE)
        display.set_pen(self.colors["WHITE"])
        vector.text("Network Status", int(width * 0.1) + offset_x, header_y)

        # Status
        self.draw_label_value(display, vector, "Status:", status_text, row1_y, status_color, width, height, offset_x)

        # IP
        config = self.wm.get_config()
        ip = config[0] if config else "0.0.0.0"
        self.draw_label_value(display, vector, "IP:", ip if ip != "0.0.0.0" else "---", row2_y, self.colors["WHITE"], width, height, offset_x)

        # AP Mode: Show SSID and Password
        if is_ap_mode:
            self.draw_label_value(display, vector, "SSID:", WiFiConfig.AP_SSID, row3_y, self.colors["CYAN"], width, height, offset_x)
            self.draw_label_value(display, vector, "Pass:", WiFiConfig.AP_PASSWORD, row4_y, self.colors["YELLOW"], width, height, offset_x)

        # Divider
        display.set_pen(self.colors["GRAY"])
        margin = int(width * 0.1)
        display.rectangle(margin + offset_x, divider_y, width - (margin * 2), 2)

        # Reset AP Mode Button - smaller size
        btn_w = 90
        btn_h = 22
        btn_center_x = width // 2 + offset_x
        
        # Button text and color based on confirmation state
        if self.confirm_pending:
            btn_text = "Tap to Confirm"
            btn_bg = self.colors["ORANGE"]
        else:
            btn_text = "Reset AP"
            btn_bg = self.colors["RED"]

        self.draw_button(
            display, vector,
            btn_text,
            btn_center_x, button_y, btn_w, btn_h,
            btn_bg,
            self.colors["WHITE"]
        )


