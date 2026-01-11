import uasyncio as asyncio
import usocket as socket

class DNSServer:
    """
    A minimal asynchronous DNS server for Captive Portal functionality.
    It intercepts all DNS queries and redirects them to a specific IP address (DNS Hijacking).
    """
    def __init__(self, ip_address):
        """
        Initialize the DNS server.

        Args:
            ip_address (str): The local IP address to redirect all queries to (e.g., '192.168.4.1').
        """
        self.ip_address = ip_address
        self._running = False
        self._task = None

    def start(self):
        """Starts the DNS server background task."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._run())
            print(f"DNSServer: Started (Redirecting all queries to {self.ip_address})")

    def stop(self):
        """Stops the DNS server and cancels the background task."""
        self._running = False
        if self._task:
            self._task.cancel()
        print("DNSServer: Stopped")

    async def _run(self):
        """Main loop for the DNS server listening on UDP port 53."""
        # Create a non-blocking UDP socket
        udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udps.setblocking(False)
        
        try:
            udps.bind(('0.0.0.0', 53))
        except Exception as e:
            print(f"DNSServer: Failed to bind port 53: {e}")
            udps.close()
            return

        while self._running:
            try:
                # Use polling to check for incoming data without blocking the asyncio loop
                data, addr = None, None
                try:
                    data, addr = udps.recvfrom(1024)
                except OSError:
                    pass # No data available at this tick

                if data and addr:
                    response = self._make_response(data)
                    if response:
                        udps.sendto(response, addr)
                
                await asyncio.sleep_ms(100) # Yield control to other coroutines
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"DNSServer: Error handling request: {e}")
                await asyncio.sleep(1)

        udps.close()

    def _make_response(self, request):
        """
        Constructs a minimal DNS response (A record) pointing to the local IP.

        Args:
            request (bytes): The raw DNS request packet.

        Returns:
            bytes: The constructed DNS response packet.
        """
        try:
            # DNS Header
            tid = request[0:2] # Transaction ID
            flags = b'\x81\x80' # Standard query response, No error
            qdcount = request[4:6] # Questions count (usually 1)
            ancount = b'\x00\x01' # Answer count (1)
            nscount = b'\x00\x00'
            arcount = b'\x00\x00'
            
            packet = tid + flags + qdcount + ancount + nscount + arcount
            
            # Answer Section using Compression Pointer (0xc00c)
            # Offset 12 points to the domain name in the question section
            dns_answer_name_ptr = b'\xc0\x0c'
            dns_answer_type = b'\x00\x01' # Type A (Host Address)
            dns_answer_class = b'\x00\x01' # Class IN (Internet)
            dns_answer_ttl = b'\x00\x00\x00\x3c' # TTL 60 seconds
            dns_answer_len = b'\x00\x04' # IPv4 address length
            
            # Convert IP string to bytes
            ip_parts = [int(x) for x in self.ip_address.split('.')]
            dns_answer_data = bytes(ip_parts)
            
            # Copy the question section from the original request
            # We assume single question starting at offset 12
            payload = request[12:]
            
            return packet + payload + dns_answer_name_ptr + dns_answer_type + dns_answer_class + dns_answer_ttl + dns_answer_len + dns_answer_data
            
        except Exception as e:
            print(f"DNSServer: Response generation error: {e}")
            return None