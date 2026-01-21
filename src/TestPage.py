from ui_framework import Page, get_colors, BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_D
from picovector import HALIGN_CENTER, VALIGN_MIDDLE
import time

class TestPage(Page):
    def __init__(self, app_manager):
        super().__init__("Test", app_manager)
        self.colors = get_colors(app_manager.display)
        self.message = "Press Buttons"
        self.last_press = "None"
        
        # Register buttons
        self.register_button_callback(BUTTON_A, self.on_press_a)
        self.register_button_callback(BUTTON_B, self.on_press_b)
        self.register_button_callback(BUTTON_C, self.on_press_c)
        self.register_button_callback(BUTTON_D, self.on_press_d)

    def on_press_a(self):
        self.message = "Button A Pressed!"
        self.last_press = "A"
        print("TestPage: Button A action triggered")

    def on_press_b(self):
        self.message = "Button B Pressed!"
        self.last_press = "B"
        print("TestPage: Button B action triggered")

    def on_press_c(self):
        self.message = "Button C Pressed!"
        self.last_press = "C"
        print("TestPage: Button C action triggered")
        
    def on_press_d(self):
        self.message = "Button D Pressed!"
        self.last_press = "D"
        print("TestPage: Button D action triggered")

    def draw(self, display, vector, offset_x=0):
        width, height = display.get_bounds()
        
        # Background
        # display.set_pen(self.colors["BLACK"])
        # display.clear() # Usually handled by AppManager
        
        # Title
        vector.set_font_size(30)
        vector.set_font_align(HALIGN_CENTER | VALIGN_MIDDLE)
        display.set_pen(self.colors["WHITE"])
        vector.text("Button Test", (width // 2) + offset_x, int(height * 0.2))
        
        # Message
        vector.set_font_size(24)
        display.set_pen(self.colors["GREEN"])
        vector.text(self.message, (width // 2) + offset_x, int(height * 0.5))
        
        # Footer
        vector.set_font_size(18)
        display.set_pen(self.colors["GRAY"])
        vector.text(f"Last: {self.last_press}", (width // 2) + offset_x, int(height * 0.8))
