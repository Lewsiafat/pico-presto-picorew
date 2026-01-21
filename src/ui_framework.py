import uasyncio as asyncio
import time
from presto import Presto
from config import UIConfig

def get_colors(display):
    """Helper to create pens from config palette."""
    pens = {}
    for name, rgb in UIConfig.COLOR_PALETTE.items():
        pens[name] = display.create_pen(*rgb)
    return pens

class Page:
    """
    Abstract base class for all pages.
    """
    def __init__(self, name, app_manager):
        self.name = name
        self.app = app_manager

    def enter(self):
        """Called when the page becomes active."""
        print(f"Entering page: {self.name}")

    def on_tap(self):
        """Called when the screen is tapped."""
        pass
        
    def exit(self):
        """Called when the page is left."""
        print(f"Exiting page: {self.name}")

    async def update(self):
        """Called periodically to update page logic."""
        pass

    def draw(self, display, vector, offset_x=0):
        """Called to render the page."""
        pass

# UI States
UI_STATE_NORMAL = 0
UI_STATE_SLIDE_LEFT = 1  # Next page comes from Right
UI_STATE_SLIDE_RIGHT = 2 # Next page comes from Left
UI_STATE_FADE_OUT = 3 # Kept if needed, but unused now
UI_STATE_FADE_IN = 4

class AppManager:
    """
    Manages pages and touch input for navigation.
    """
    def __init__(self, presto, wifi_manager):
        self.presto = presto
        self.display = presto.display
        self.touch = presto.touch
        self.wm = wifi_manager
        
        self.pages = []
        self.current_page_index = 0
        self.running = True
        
        # Touch handling
        self.touch_start_x = 0
        self.last_touch_x = 0
        self.touch_start_time = 0
        self.min_swipe_dist = 40
        self.max_swipe_time = 500
        
        # Transitions
        self.ui_state = UI_STATE_NORMAL
        self.next_page_index = -1
        self.slide_pixel_offset = 0
        self.slide_speed = 40 # Pixels per frame

    def add_page(self, page):
        self.pages.append(page)

    def switch_page(self, index):
        if 0 <= index < len(self.pages):
            # If already on this page (and stable), ignore
            if index == self.current_page_index and self.ui_state == UI_STATE_NORMAL:
                return
            
            # If already transitioning to this page, ignore (prevent reset)
            if self.ui_state != UI_STATE_NORMAL and index == self.next_page_index:
                return
                
            # Determine Direction
            self.next_page_index = index
            if index > self.current_page_index:
                self.ui_state = UI_STATE_SLIDE_LEFT
            else:
                self.ui_state = UI_STATE_SLIDE_RIGHT
                
            self.slide_pixel_offset = 0
            
            # Reset touch state to prevent ghost swipes
            self.touch_start_time = 0
            
            # Pre-enter the next page so it can fetch data if needed
            self.pages[self.next_page_index].enter()

    def handle_input(self):
        # Ignore input during transitions
        if self.ui_state != UI_STATE_NORMAL:
            return

        self.touch.poll()
        
        # Disable swiping on Startup Page (index 0)
        if self.current_page_index == 0:
            return

        if self.touch.state:
            # Touch start
            if self.touch_start_time == 0:
                self.touch_start_time = time.ticks_ms()
                self.touch_start_x = self.touch.x
            
            # Continuously update last known X to avoid 0-read issues on release
            self.last_touch_x = self.touch.x
        else:
            # Touch end
            if self.touch_start_time != 0:
                touch_duration = time.ticks_diff(time.ticks_ms(), self.touch_start_time)
                
                # Use last_touch_x for distance calculation
                touch_dist = self.last_touch_x - self.touch_start_x
                
                print(f"Touch Input: Duration={touch_duration}ms, Dist={touch_dist}, StartX={self.touch_start_x}, EndX={self.last_touch_x}")
                
                # Check for swipe
                if touch_duration < self.max_swipe_time:
                    if abs(touch_dist) > self.min_swipe_dist:
                        if touch_dist < 0:
                            # Swipe Left -> Next Page
                            self.next_page()
                        else:
                            # Swipe Right -> Previous Page
                            self.prev_page()
                    else:
                        # Tap detected (short duration, small movement)
                         print("AppManager: Tap Detected!")
                         current_page = self.pages[self.current_page_index]
                         current_page.on_tap()
                
                self.touch_start_time = 0

    def next_page(self):
        # Don't loop back to Setup page (index 0)
        new_index = (self.current_page_index + 1)
        if new_index >= len(self.pages):
             new_index = 1
        self.switch_page(new_index)

    def prev_page(self):
        new_index = (self.current_page_index - 1)
        if new_index < 1:
             new_index = len(self.pages) - 1
        self.switch_page(new_index)
        
    def draw_indicators(self, width, height, offset_x=0):
        # Determine which page index to highlight based on transitions using some logic?
        # Simpler: Just draw indicators for 'current' page, and if sliding, maybe fade?
        # For now, just draw static indicators at bottom, they will slide with the page if we attach them? 
        # No, indicators usually stay static on screen.
        # Let's keep indicators STATIC on screen (no offset_x passed to them).
        
        # We need to decide WHICH dot is highlighted.
        # If sliding Left (Current -> Next), start with Current highlighted.
        # Ideally, we could animate the highlight, but static is fine for now.
        
        # Use current_page_index for highlight source.
        
        if self.current_page_index == 0:
             # If transitioning FROM 0 TO 1, maybe start showing?
             # For simplicity, if current is 0, don't show.
             return

        total_content_pages = len(self.pages) - 1
        if total_content_pages <= 1:
            return

        dot_radius = 4
        spacing = 15
        total_width = (total_content_pages - 1) * spacing
        start_x = (width // 2) - (total_width // 2)
        y = height - 20
        
        current_content_index = self.current_page_index - 1
        
        for i in range(total_content_pages):
            cx = start_x + (i * spacing)
            if i == current_content_index:
                self.display.set_pen(self.display.create_pen(255, 255, 255))
                self.display.circle(cx, y, dot_radius)
            else:
                self.display.set_pen(self.display.create_pen(100, 100, 100))
                self.display.circle(cx, y, dot_radius)

    async def run(self, vector):
        if not self.pages:
            print("No pages added!")
            return

        print("AppManager Started")
        self.pages[0].enter()
        
        width, height = self.display.get_bounds()

        while self.running:
            # 1. Update Logic
            current_page = self.pages[self.current_page_index]
            
            # Only process input and page updates if not in a slide transition
            if self.ui_state == UI_STATE_NORMAL: 
                 self.handle_input()
                 await current_page.update()

            # 2. Transition Logic & Drawing
            self.display.set_pen(self.display.create_pen(0, 0, 0))
            self.display.clear()

            if self.ui_state == UI_STATE_NORMAL:
                current_page.draw(self.display, vector, 0)
                self.draw_indicators(width, height)
                
            elif self.ui_state == UI_STATE_SLIDE_LEFT:
                # Current moving LEFT (-offset), Next moving in from RIGHT (width - offset)
                self.slide_pixel_offset += self.slide_speed
                if self.slide_pixel_offset >= width:
                    self.slide_pixel_offset = width
                    # Finish Transition
                    self.pages[self.current_page_index].exit()
                    self.current_page_index = self.next_page_index
                    self.ui_state = UI_STATE_NORMAL
                    self.slide_pixel_offset = 0
                    
                    # Draw final state
                    self.pages[self.current_page_index].draw(self.display, vector, 0)
                    self.draw_indicators(width, height)
                else:
                    # Draw Current
                    current_page.draw(self.display, vector, -self.slide_pixel_offset)
                    # Draw Next
                    self.pages[self.next_page_index].draw(self.display, vector, width - self.slide_pixel_offset)
                    # Indicators (Static)
                    self.draw_indicators(width, height)
                    
            elif self.ui_state == UI_STATE_SLIDE_RIGHT:
                # Current moving RIGHT (+offset), Next moving in from LEFT (-width + offset)
                self.slide_pixel_offset += self.slide_speed
                if self.slide_pixel_offset >= width:
                    self.slide_pixel_offset = width
                    # Finish Transition
                    self.pages[self.current_page_index].exit()
                    self.current_page_index = self.next_page_index
                    self.ui_state = UI_STATE_NORMAL
                    self.slide_pixel_offset = 0
                    
                    self.pages[self.current_page_index].draw(self.display, vector, 0)
                    self.draw_indicators(width, height)
                else:
                    # Draw Current
                    current_page.draw(self.display, vector, self.slide_pixel_offset)
                    # Draw Next
                    self.pages[self.next_page_index].draw(self.display, vector, -width + self.slide_pixel_offset)
                    self.draw_indicators(width, height)

            self.presto.update()
            await asyncio.sleep(0.01)
