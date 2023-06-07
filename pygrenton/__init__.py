import asyncio
import socket
import threading
import queue
from .cipher import GrentonCypher
from .requests import Request, CheckAlive

class GrentonApi:

    def __init__(self, ip: str, port: int, key: str | bytes, iv: str | bytes, timeout: float = 1) -> None:
        self._addr = (ip, port)
        self._timeout = timeout
        self._local_ip = socket.gethostbyname(socket.gethostname())
        self._cypher = GrentonCypher(key, iv)

        self._responses: dict = {}
        self._msg_queue: queue.Queue[tuple[Request, threading.Event]] = queue.Queue()

        self._msg_condition = threading.Condition()
        self._msg_sender_thread = threading.Thread(target=self._sender_loop, daemon=True)
        self._msg_sender_thread.start()

    async def send_request_async(self, req: Request):
        event = self._appendQueue(req)

        event.wait()
        resp = self._responses.pop(req._id)
        
        if isinstance(resp, Exception):
            raise resp
        
        return req.parse_response(resp)

    def send_request(self, req: Request):
        return asyncio.run(self.send_request_async(req))

    def checkAlive(self) -> bool:
        try:
            self.send_request(CheckAlive())
            return True
        except:
            return False

    def ip(self) -> str:
        return self._addr[0]

    def port(self) -> int:
        return self._addr[1]
    
    def _appendQueue(self, req: Request):
        with self._msg_condition:
            resp_event = threading.Event()

            self._msg_queue.put((req, resp_event))
            self._msg_condition.notify_all()

            return resp_event
    
    def _sender_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self._timeout)

        while True:
            with self._msg_condition:
                self._msg_condition.wait_for(lambda: not self._msg_queue.empty())
                req, resp_event = self._msg_queue.get()

            payload = self._cypher.encrypt(bytes(req.create_request(self._local_ip), "utf-8"))

            try:
                sock.sendto(payload, self._addr)
                
                resp = sock.recvfrom(1024)[0]
                resp = self._cypher.decrypt(resp).decode("utf-8")

                self._responses[req._id] = resp

            except Exception as e:
                self._responses[req._id] = e
                
            resp_event.set()

