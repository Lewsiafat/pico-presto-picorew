import uasyncio as asyncio

class WebServer:
    """
    A lightweight asynchronous HTTP server designed for device provisioning.
    Supports basic routing, header parsing, and URL-encoded body parameters.
    """
    def __init__(self):
        self._routes = {}
        self._running = False
        self._server = None

    def add_route(self, path, handler, method="GET"):
        """
        Register a handler for a specific URL path and HTTP method.

        Args:
            path (str): The URL path (e.g., '/').
            handler (callable): Async function to handle the request.
            method (str): HTTP method (default 'GET').
        """
        self._routes[(path, method)] = handler

    async def start(self, host='0.0.0.0', port=80):
        """Starts the asynchronous HTTP server."""
        if not self._running:
            self._running = True
            print(f"WebServer: Starting on {host}:{port}")
            self._server = await asyncio.start_server(self._handle_client, host, port)

    def stop(self):
        """Stops the HTTP server."""
        if self._running and self._server:
            self._server.close()
            self._running = False
            print("WebServer: Stopped")

    async def _handle_client(self, reader, writer):
        """Internal handler for individual client connections."""
        try:
            request_line = await reader.readline()
            if not request_line:
                writer.close()
                return

            # Decode and parse the first line of the request
            request_line = request_line.decode().strip()
            if not request_line:
                 writer.close()
                 return
                 
            parts = request_line.split(" ", 2)
            if len(parts) < 2:
                writer.close()
                return
            method, path = parts[0], parts[1]
            
            # Read and parse headers to extract content length for POST requests
            headers = {}
            content_length = 0
            while True:
                line = await reader.readline()
                if not line or line == b'\r\n':
                    break
                
                line_str = line.decode().strip()
                if ':' in line_str:
                    key, value = line_str.split(":", 1)
                    key = key.lower().strip()
                    headers[key] = value.strip()
                    if key == 'content-length':
                        try:
                            content_length = int(value.strip())
                        except ValueError:
                            content_length = 0

            # Read Body if it's a POST request
            body = ""
            if method == "POST" and content_length > 0:
                body_bytes = await reader.read(content_length)
                body = body_bytes.decode()

            # Construct request context
            request = {
                "method": method,
                "path": path,
                "headers": headers,
                "body": body,
                "params": self._parse_params(body) if body else {}
            }
            
            # Find and execute the registered route handler
            handler = self._routes.get((path, method))
            
            # Captive Portal Fallback: redirect any unknown GET requests to the root
            if not handler and method == "GET":
                 handler = self._routes.get(("/", "GET"))
            
            if handler:
                response = await handler(request)
                writer.write(response)
                await writer.drain()
            else:
                writer.write(b"HTTP/1.1 404 Not Found\r\n\r\nNot Found")
                await writer.drain()
                
        except Exception as e:
            print(f"WebServer: Handler error: {e}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass

    def _parse_params(self, body):
        """
        Parses URL-encoded form data from the request body.

        Args:
            body (str): The raw body string.

        Returns:
            dict: Parsed key-value pairs.
        """
        params = {}
        if not body: return params
        try:
            pairs = body.split('&')
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    # Basic URL-decoding: replace '+' with space and decode '%' sequences
                    value = value.replace('+', ' ')
                    parts = value.split('%')
                    decoded_value = parts[0]
                    for part in parts[1:]:
                        if len(part) >= 2:
                            try:
                                char_code = int(part[:2], 16)
                                decoded_value += chr(char_code) + part[2:]
                            except ValueError:
                                decoded_value += '%' + part
                        else:
                            decoded_value += '%' + part
                    params[key] = decoded_value
        except Exception as e:
            print(f"WebServer: Parameter parsing error: {e}")
        return params
