class WiFiConfig:
    """Configuration constants for WiFi connection and AP mode."""
    # Maximum number of connection attempts before entering FAIL state
    MAX_RETRIES = 5
    
    # Time (seconds) to wait for connection per attempt
    CONNECT_TIMEOUT = 15
    
    # Time (seconds) to wait between retries in CONNECTING state
    RETRY_DELAY = 2
    
    # Time (seconds) to wait in FAIL state before trying again (Auto-recovery)
    FAIL_RECOVERY_DELAY = 30
    
    # Interval (seconds) to check connection health in CONNECTED state
    HEALTH_CHECK_INTERVAL = 2
    
    # AP Mode Settings for Provisioning
    AP_SSID = "Picore-W-Setup"
    AP_PASSWORD = "password123" # Default secure password
    AP_IP = "192.168.4.1"
class UIConfig:
    """Configuration for UI appearance and behavior."""
    STARTUP_DURATION = 3000
    CRYPTO_REFRESH_INTERVAL = 20
    CRYPTO_API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
    
    # RGB Colors
    COLOR_PALETTE = {
        "BLACK": (0, 0, 0),
        "WHITE": (255, 255, 255),
        "GRAY": (50, 50, 50),
        "GREEN": (0, 255, 0),
        "RED": (255, 50, 50),
        "ORANGE": (255, 165, 0),
        "BLUE": (50, 150, 255),
        "YELLOW": (255, 215, 0),
        "CYAN": (0, 255, 255)
    }

class WeatherConfig:
    """Configuration for Weather updates (Open-Meteo)."""
    # Default: Taipei, Taiwan
    LATITUDE = 25.0330 
    LONGITUDE = 121.5654
    UPDATE_INTERVAL = 900 # 15 minutes (900 seconds)
    
    # API URL (Dynamically constructed in Page, but base config here if needed or just use params)
    API_URL = "https://api.open-meteo.com/v1/forecast"
