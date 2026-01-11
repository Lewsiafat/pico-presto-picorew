import json
import os
import time

CONFIG_FILE = "wifi_config.json"

class ConfigManager:
    """
    Manages persistent storage of WiFi configuration data using a JSON file on the Flash filesystem.
    """
    
    @staticmethod
    def load_config():
        """
        Loads configuration from the JSON file.

        Returns:
            dict: Configuration data containing 'ssid' and 'password', or None if file doesn't exist or is invalid.
        """
        try:
            try:
                os.stat(CONFIG_FILE)
            except OSError:
                # File does not exist
                return None
                
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                return config
                
        except (ValueError, OSError) as e:
            # Handle potential file corruption or access errors silently or with minimal logging
            print(f"ConfigManager: Error loading config: {e}")
            return None

    @staticmethod
    def save_config(ssid, password):
        """
        Saves WiFi credentials to the JSON file with verification.

        Args:
            ssid (str): The WiFi SSID to save.
            password (str): The WiFi password to save.

        Returns:
            bool: True if save was successful and verified, False otherwise.
        """
        config_data = {
            "ssid": ssid,
            "password": password
        }
        
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config_data, f)
                f.flush() # Ensure data is written to the flash buffer
            
            # Verification step: read back the file to ensure it was saved correctly
            time.sleep(0.1)
            with open(CONFIG_FILE, "r") as f:
                saved_data = json.load(f)
                if saved_data.get("ssid") == ssid:
                    return True
                else:
                    print("ConfigManager: Verification FAILED. Content mismatch.")
                    return False
                    
        except OSError as e:
            print(f"ConfigManager: Error saving config: {e}")
            return False
        except Exception as e:
            print(f"ConfigManager: Unexpected error during save: {e}")
            return False

    @staticmethod
    def delete_config():
        """
        Removes the configuration file (performs a factory reset of network settings).

        Returns:
            bool: True if the file was deleted, False if it didn't exist or an error occurred.
        """
        try:
            os.remove(CONFIG_FILE)
            return True
        except OSError:
            return False
