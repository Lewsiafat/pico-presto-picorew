import uasyncio as asyncio
from presto import Presto
from picovector import ANTIALIAS_BEST, PicoVector
from ui_framework import AppManager
from wifi_manager import WiFiManager
from StatusPage import StatusPage
from CryptoPage import CryptoPage
from WeatherPage import WeatherPage
from ClockPage import ClockPage
from StartupPage import StartupPage
import gc

async def main():
    """
    Main entry point for Picore-W.
    Initializes hardware, network, and UI.
    """
    print("--- Picore-W Initializing ---")
    
    # 1. Initialize Hardware (Presto)
    try:
        presto = Presto(ambient_light=True)
        display = presto.display
        
        # Setup Vector Graphics
        vector = PicoVector(display)
        vector.set_antialiasing(ANTIALIAS_BEST)
        vector.set_font("Roboto-Medium.af", 20)
        
    except Exception as e:
        print(f"Error initializing hardware: {e}")
        return

    # 2. Initialize WiFi Manager (starts its own state machine task)
    wm = WiFiManager()
    
    # 3. Initialize UI Framework
    app_manager = AppManager(presto, wm)
    
    # 4. Add Pages
    # Page 0: Startup (3s delay)
    app_manager.add_page(StartupPage(app_manager))
    # Page 1: Status
    app_manager.add_page(StatusPage(app_manager))
    # Page 4: Clock
    app_manager.add_page(ClockPage(app_manager))
    # Page 2: Crypto Ticker
    app_manager.add_page(CryptoPage(app_manager))
    # Page 3: Weather
    app_manager.add_page(WeatherPage(app_manager))
   
    
    # 5. Run App
    await app_manager.run(vector)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n--- System Stopped ---")