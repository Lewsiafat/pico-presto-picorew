import usocket as socket
import uasyncio as asyncio
import ubinascii
import urandom
import uselect

class WebSocket:
    def __init__(self, uri):
        self.uri = uri
        self.sock = None
        self.ssl = False
        
        proto, dummy, host, path = uri.split("/", 3)
        self.host = host
        self.path = "/" + path
        if proto == "wss:":
            self.ssl = True
            self.port = 443
        else:
            self.port = 80
            
        if ":" in self.host:
            self.host, port = self.host.split(":")
            self.port = int(port)

    async def connect(self):
        # Blocking connect for reliability during handshake
        ai = socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM)
        ai = ai[0]
        
        self.sock = socket.socket(ai[0], ai[1], ai[2])
        # self.sock.setblocking(False) # Keep blocking for setup
        
        try:
            self.sock.connect(ai[-1])
        except OSError as e:
            self.close()
            raise e

        if self.ssl:
            import ssl
            # Wrap socket (blocking)
            self.sock = ssl.wrap_socket(self.sock, server_hostname=self.host)

        key = ubinascii.b2a_base64(bytes(urandom.getrandbits(8) for _ in range(16)))[:-1]

        header = (
            "GET {} HTTP/1.1\r\n"
            "Host: {}:{}\r\n"
            "Connection: Upgrade\r\n"
            "Upgrade: websocket\r\n"
            "Sec-WebSocket-Key: {}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        ).format(self.path, self.host, self.port, key)

        # Send header (blocking)
        self.sock.write(header.encode())

        # Read handshake (blocking)
        header_data = b""
        while b"\r\n\r\n" not in header_data:
            chunk = self.sock.read(1)
            if not chunk:
                raise OSError("Connection closed during handshake")
            header_data += chunk

        if not header_data.startswith(b"HTTP/1.1 101"):
             raise OSError("WebSocket handshake failed")
             
        # Switch to non-blocking for asyncio usage
        self.sock.setblocking(False)

    async def _send(self, data):
        # Non-blocking send loop
        total_sent = 0
        while total_sent < len(data):
            try:
                sent = self.sock.write(data[total_sent:])
                if sent is None: 
                    await asyncio.sleep(0.01)
                    continue
                total_sent += sent # MicroPython write returns bytes written or None
            except OSError as e:
                if e.args[0] == 11: # EAGAIN
                    await asyncio.sleep(0.01)
                else:
                    raise e

    async def recv_bytes(self, n):
        # Non-blocking read loop
        data = b""
        while len(data) < n:
            try:
                chunk = self.sock.read(n - len(data))
                if chunk is None or chunk == b"":
                    if chunk == b"":
                         return b"" # Closed
                    await asyncio.sleep(0.01)
                    continue
                data += chunk
            except OSError as e:
                if e.args[0] == 11:
                    await asyncio.sleep(0.01)
                else:
                    raise e
        return data

    async def send(self, data):
        payload = data.encode('utf-8')
        length = len(payload)
        header = b'\x81' 
        
        if length < 126:
            header += bytes([0x80 | length])
        elif length < 65536:
            header += bytes([0x80 | 126]) + length.to_bytes(2, 'big')
        else:
            header += bytes([0x80 | 127]) + length.to_bytes(8, 'big')

        mask = bytes(urandom.getrandbits(8) for _ in range(4))
        masked_payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        
        await self._send(header + mask + masked_payload)

    async def recv(self):
        first_byte = await self.recv_bytes(1)
        if not first_byte: return None
        
        opcode = first_byte[0] & 0x0F
        if opcode == 8: # Close
            self.close()
            return None
            
        second_byte = await self.recv_bytes(1)
        if not second_byte: return None
        
        length = second_byte[0] & 0x7F
        
        if length == 126:
            lb = await self.recv_bytes(2)
            length = int.from_bytes(lb, 'big')
        elif length == 127:
            lb = await self.recv_bytes(8)
            length = int.from_bytes(lb, 'big')
            
        payload = await self.recv_bytes(length)
        return payload.decode('utf-8')

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None
