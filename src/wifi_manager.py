import network
import uasyncio as asyncio
import time
import machine
from config_manager import ConfigManager
from dns_server import DNSServer
from web_server import WebServer
from constants import *
from config import WiFiConfig

class WiFiManager:
    """
    Core WiFi management system. 
    Handles connection lifecycles, retries, and web-based provisioning.
    """
    def __init__(self):
        # Station interface for connecting to existing networks
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        
        # Access Point interface for provisioning mode
        self.ap = network.WLAN(network.AP_IF)
        self.ap.active(False)
        
        # Network services
        self.dns_server = DNSServer(WiFiConfig.AP_IP)
        self.web_server = WebServer()
        self._setup_routes()

        # Internal state
        self._state = STATE_IDLE
        self._target_ssid = None
        self._target_password = None
        self._retry_count = 0
        
        # Start the background state machine task
        asyncio.create_task(self._run_state_machine())

    def _setup_routes(self):
        """Register routes for the provisioning web server."""
        self.web_server.add_route("/", self._handle_root_request)
        self.web_server.add_route("/hotspot-detect.html", self._handle_root_request) # Apple
        self.web_server.add_route("/generate_204", self._handle_root_request) # Android
        self.web_server.add_route("/configure", self._handle_configure, method="POST")

    def _read_template(self, name):
        """Read a template file from templates/ directory."""
        paths = [f"templates/{name}.html", f"src/templates/{name}.html"]
        for path in paths:
            try:
                with open(path, "r") as f:
                    return f.read()
            except OSError:
                continue
        return f"Error: Template {name} not found in {paths}"

    async def _handle_root_request(self, request):
        """Serve the main provisioning page."""
        html = self._read_template("provision")
        return ("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html).encode()

    async def _handle_configure(self, request):
        """Process form submission from the provisioning page."""
        params = request.get("params", {})
        ssid = params.get("ssid")
        password = params.get("password")
        
        if ssid:
            # Save configuration to flash immediately
            success = ConfigManager.save_config(ssid, password)
            if success:
                # Schedule a reboot to apply changes
                asyncio.create_task(self._reboot_device())
                html = self._read_template("success")
                return ("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html).encode()
            else:
                return b"HTTP/1.1 500 Internal Server Error\r\n\r\nFailed to save configuration"
        else:
            return b"HTTP/1.1 400 Bad Request\r\n\r\nMissing SSID"

    async def _reboot_device(self):
        """Delayed reboot to allow HTTP response to be sent."""
        print("WiFiManager: Settings updated. Rebooting in 3 seconds...")
        await asyncio.sleep(3)
        machine.reset()

    async def _run_state_machine(self):
        """Main asynchronous loop for WiFi state transitions."""
        print("WiFiManager: State Machine Started")
        self._load_and_connect()
        while True:
            try:
                if self._state == STATE_IDLE:
                    await asyncio.sleep(1)
                elif self._state == STATE_CONNECTING:
                    await self._handle_connecting()
                elif self._state == STATE_CONNECTED:
                    await self._handle_connected()
                elif self._state == STATE_FAIL:
                    await self._handle_fail()
                elif self._state == STATE_AP_MODE:
                    await self._handle_ap_mode()
            except Exception as e:
                print(f"WiFiManager: State machine error: {e}")
                await asyncio.sleep(5)
            await asyncio.sleep(0.1)

    def _load_and_connect(self):
        """Attempt to load credentials and start connection sequence."""
        config = ConfigManager.load_config()
        if config and "ssid" in config and "password" in config:
            print(f"WiFiManager: Found saved config for '{config['ssid']}'. Connecting...")
            self.connect(config["ssid"], config["password"])
        else:
            print("WiFiManager: No saved config found. Entering Provisioning (AP) Mode.")
            self._state = STATE_AP_MODE

    async def _handle_connecting(self):
        """Manage connection attempts and retries."""
        self._stop_ap_services()
        
        print(f"WiFiManager: Connecting to {self._target_ssid} (Attempt {self._retry_count + 1}/{WiFiConfig.MAX_RETRIES})...")
        self.wlan.connect(self._target_ssid, self._target_password)
        
        start_time = time.time()
        while (time.time() - start_time) < WiFiConfig.CONNECT_TIMEOUT:
            if self.wlan.isconnected():
                print("WiFiManager: Connection Successful!")
                self._state = STATE_CONNECTED
                self._retry_count = 0
                return
            
            status = self.wlan.status()
            # Stop early if explicit failure is detected
            if status == network.STAT_CONNECT_FAIL or status == network.STAT_NO_AP_FOUND or status == network.STAT_WRONG_PASSWORD:
                break
            await asyncio.sleep(0.5)
            
        self._retry_count += 1
        if self._retry_count >= WiFiConfig.MAX_RETRIES:
            print("WiFiManager: Connection failed after multiple attempts.")
            self._state = STATE_FAIL
        else:
            self.wlan.disconnect()
            await asyncio.sleep(WiFiConfig.RETRY_DELAY)

    async def _handle_connected(self):
        """Monitor connection health when connected."""
        if not self.wlan.isconnected():
            print("WiFiManager: Connection lost. Reconnecting...")
            self.wlan.disconnect()
            self._retry_count = 0
            self._state = STATE_CONNECTING
        else:
            await asyncio.sleep(WiFiConfig.HEALTH_CHECK_INTERVAL)

    async def _handle_fail(self):
        """Handle failure state with recovery delay."""
        for _ in range(WiFiConfig.FAIL_RECOVERY_DELAY):
            if self._state != STATE_FAIL: return 
            await asyncio.sleep(1)
        self._retry_count = 0
        self._state = STATE_CONNECTING

    async def _handle_ap_mode(self):
        """Manage Access Point and related services."""
        if not self.ap.active():
            print(f"WiFiManager: Enabling Access Point (SSID: {WiFiConfig.AP_SSID})...")
            self.ap.config(essid=WiFiConfig.AP_SSID, password=WiFiConfig.AP_PASSWORD)
            self.ap.active(True)
            
            while not self.ap.active():
                await asyncio.sleep(0.1)
            
            current_ip = self.ap.ifconfig()[0]
            print(f"WiFiManager: AP Mode active at {current_ip}")
            
            self.dns_server.ip_address = current_ip
            self.dns_server.start()
            await self.web_server.start(host='0.0.0.0', port=80)
        
        await asyncio.sleep(2)

    def _stop_ap_services(self):
        """Ensure AP and its services are stopped."""
        if self.ap.active():
            self.dns_server.stop()
            self.web_server.stop()
            self.ap.active(False)

    def connect(self, ssid, password):
        """Trigger a connection request."""
        self._target_ssid = ssid
        self._target_password = password
        self._retry_count = 0
        self._state = STATE_CONNECTING

    def disconnect(self):
        """Disconnect from WiFi and stop all services."""
        if self.wlan.isconnected():
            self.wlan.disconnect()
        self._state = STATE_IDLE
        self._retry_count = 0
        self._stop_ap_services()

    def is_connected(self):
        """Check if currently connected to WiFi."""
        return self._state == STATE_CONNECTED

    def get_status(self):
        """Get the current state machine state."""
        return self._state
        
    def get_config(self):
        """Get current IP configuration."""
        return self.wlan.ifconfig()