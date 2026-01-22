from ui_framework import Page, get_colors
from param_store import get_params
from picovector import HALIGN_LEFT, HALIGN_CENTER, HALIGN_RIGHT, VALIGN_MIDDLE

class SettingsPage(Page):
    """
    Settings page for modifying app parameters.
    - Tap item to select
    - Tap selected item to enter edit mode
    - Tap +/- buttons in edit mode to adjust value
    - Tap elsewhere to exit edit mode
    """

    def __init__(self, app_manager):
        super().__init__("Settings", app_manager)
        self.colors = get_colors(app_manager.display)
        self.params = get_params()

        # Settings items configuration
        # Each item: (key, label, step, min_val, max_val, decimals)
        self.items = [
            ("timezone_offset", "Timezone", 1, -12, 14, 0),
            ("weather_latitude", "Latitude", 0.1, -90.0, 90.0, 2),
            ("weather_longitude", "Longitude", 0.1, -180.0, 180.0, 2),
            ("weather_interval", "Weather Int", 60, 60, 3600, 0),
            ("clock_mode", "Clock Mode", 1, 0, 1, 0),
        ]

        self.selected_index = -1  # -1 = no selection
        self.edit_mode = False

        # UI layout constants
        self.header_y = 30
        self.list_start_y = 60
        self.item_height = 32
        self.button_y = 230
        self.button_width = 60
        self.button_height = 40

    def enter(self):
        super().enter()
        self.selected_index = -1
        self.edit_mode = False

    def exit(self):
        super().exit()
        self.edit_mode = False

    def _get_display_value(self, key, decimals):
        """Format parameter value for display."""
        val = self.params.get(key)
        if key == "timezone_offset":
            sign = "+" if val >= 0 else ""
            return f"UTC{sign}{val}"
        elif key == "clock_mode":
            return "Digital" if val == 0 else "Analog"
        elif decimals > 0:
            return f"{val:.{decimals}f}"
        else:
            return str(int(val))

    def _adjust_value(self, delta):
        """Adjust the selected parameter value by delta * step."""
        if self.selected_index < 0 or not self.edit_mode:
            return

        key, _, step, min_val, max_val, _ = self.items[self.selected_index]
        current = self.params.get(key)
        new_val = current + (delta * step)

        # Clamp to range
        new_val = max(min_val, min(max_val, new_val))

        # Round to avoid float precision issues
        if isinstance(step, float):
            new_val = round(new_val, 4)

        self.params.set(key, new_val)
        print(f"SettingsPage: {key} = {new_val}")

    def on_tap(self):
        """Handle tap events from AppManager."""
        touch = self.app.touch
        x, y = touch.x, touch.y
        width, _ = self.app.display.get_bounds()

        # Check button area (edit mode only)
        if self.edit_mode and self.button_y <= y <= self.button_y + self.button_height:
            btn_margin = 40
            minus_x = btn_margin
            plus_x = width - btn_margin - self.button_width

            if minus_x <= x <= minus_x + self.button_width:
                self._adjust_value(-1)
                return
            elif plus_x <= x <= plus_x + self.button_width:
                self._adjust_value(1)
                return

        # Check list items
        for i, _ in enumerate(self.items):
            item_y = self.list_start_y + (i * self.item_height)
            if item_y <= y <= item_y + self.item_height:
                if self.selected_index == i:
                    # Already selected - toggle edit mode
                    self.edit_mode = not self.edit_mode
                else:
                    # Select this item
                    self.selected_index = i
                    self.edit_mode = False
                return

        # Tap elsewhere - exit edit mode but keep selection
        if self.edit_mode:
            self.edit_mode = False

    def draw(self, display, vector, offset_x=0):
        width, height = display.get_bounds()

        # Header
        vector.set_font_size(18)
        vector.set_font_align(HALIGN_LEFT | VALIGN_MIDDLE)
        display.set_pen(self.colors["WHITE"])
        vector.text("Settings", 15 + offset_x, self.header_y)

        # List items
        vector.set_font_size(14)
        label_x = 15
        value_x = 180  # Fixed position for values

        for i, (key, label, _, _, _, decimals) in enumerate(self.items):
            item_y = self.list_start_y + (i * self.item_height)
            is_selected = (i == self.selected_index)

            # Selection indicator and highlight
            if is_selected:
                if self.edit_mode:
                    # Edit mode - orange highlight
                    display.set_pen(self.colors["ORANGE"])
                    display.rectangle(offset_x + 10, item_y, width - 20, self.item_height - 2)
                    display.set_pen(self.colors["BLACK"])
                else:
                    # Selected - gray highlight
                    display.set_pen(self.colors["GRAY"])
                    display.rectangle(offset_x + 10, item_y, width - 20, self.item_height - 2)
                    display.set_pen(self.colors["WHITE"])
            else:
                display.set_pen(self.colors["WHITE"])

            # Label (with arrow if selected)
            vector.set_font_align(HALIGN_LEFT | VALIGN_MIDDLE)
            prefix = "> " if is_selected else "  "
            vector.text(prefix + label, offset_x + label_x, item_y + (self.item_height // 2))

            # Value (fixed position, left aligned)
            value_str = self._get_display_value(key, decimals)
            vector.text(value_str, offset_x + value_x, item_y + (self.item_height // 2))

        # Edit mode buttons
        if self.edit_mode:
            btn_margin = 40
            minus_x = btn_margin + offset_x
            plus_x = width - btn_margin - self.button_width + offset_x

            # Minus button
            display.set_pen(self.colors["CYAN"])
            display.rectangle(minus_x, self.button_y, self.button_width, self.button_height)
            display.set_pen(self.colors["BLACK"])
            vector.set_font_size(20)
            vector.set_font_align(HALIGN_CENTER | VALIGN_MIDDLE)
            vector.text("-", minus_x + (self.button_width // 2), self.button_y + (self.button_height // 2))

            # Plus button
            display.set_pen(self.colors["CYAN"])
            display.rectangle(plus_x, self.button_y, self.button_width, self.button_height)
            display.set_pen(self.colors["BLACK"])
            vector.text("+", plus_x + (self.button_width // 2), self.button_y + (self.button_height // 2))

            # Current selected item hint
            if self.selected_index >= 0:
                key, label, step, min_val, max_val, _ = self.items[self.selected_index]
                hint = f"Step:{step} Range:{min_val}~{max_val}"
                vector.set_font_size(10)
                display.set_pen(self.colors["GRAY"])
                vector.set_font_align(HALIGN_CENTER | VALIGN_MIDDLE)
                vector.text(hint, (width // 2) + offset_x, self.button_y + self.button_height + 12)
