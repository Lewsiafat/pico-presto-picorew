import json

# Singleton instance
_params_instance = None

def get_params():
    """Get the singleton ParamStore instance."""
    global _params_instance
    if _params_instance is None:
        _params_instance = ParamStore()
    return _params_instance


class ParamStore:
    """
    Parameter store with observer pattern for two-way binding.
    Automatically persists changes to app_params.json.
    """

    STORAGE_FILE = "app_params.json"

    # Default parameter values
    DEFAULTS = {
        "timezone_offset": 8,       # UTC+8 (Taipei)
        "weather_latitude": 25.0330,
        "weather_longitude": 121.5654,
        "weather_interval": 900,    # 15 minutes in seconds
        "clock_mode": 0,            # 0=Digital, 1=Analog
    }

    def __init__(self):
        self._params = {}
        self._subscribers = {}  # key -> list of callbacks
        self._load()

    def _load(self):
        """Load parameters from storage, using defaults for missing keys."""
        try:
            with open(self.STORAGE_FILE, "r") as f:
                stored = json.load(f)
                # Merge with defaults
                self._params = dict(self.DEFAULTS)
                self._params.update(stored)
                print(f"ParamStore: Loaded from {self.STORAGE_FILE}")
        except (OSError, ValueError) as e:
            print(f"ParamStore: Using defaults ({e})")
            self._params = dict(self.DEFAULTS)
            self._save()

    def _save(self):
        """Persist current parameters to storage."""
        try:
            with open(self.STORAGE_FILE, "w") as f:
                json.dump(self._params, f)
            print("ParamStore: Saved")
        except OSError as e:
            print(f"ParamStore: Save failed ({e})")

    def get(self, key, default=None):
        """Get parameter value by key."""
        return self._params.get(key, default)

    def set(self, key, value):
        """Set parameter value and notify subscribers."""
        old_value = self._params.get(key)
        if old_value != value:
            self._params[key] = value
            self._save()
            self._notify(key, value, old_value)

    def subscribe(self, key, callback):
        """
        Subscribe to parameter changes.
        Callback signature: callback(new_value, old_value)
        """
        if key not in self._subscribers:
            self._subscribers[key] = []
        if callback not in self._subscribers[key]:
            self._subscribers[key].append(callback)

    def unsubscribe(self, key, callback):
        """Unsubscribe from parameter changes."""
        if key in self._subscribers:
            try:
                self._subscribers[key].remove(callback)
            except ValueError:
                pass

    def _notify(self, key, new_value, old_value):
        """Notify all subscribers of a parameter change."""
        if key in self._subscribers:
            for callback in self._subscribers[key]:
                try:
                    callback(new_value, old_value)
                except Exception as e:
                    print(f"ParamStore: Callback error for '{key}': {e}")

    def get_all_keys(self):
        """Return list of all parameter keys."""
        return list(self._params.keys())
