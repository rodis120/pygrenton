import asyncio
import socket
import threading
import queue
import random
from .cipher import GrentonCypher

class CluMessage:
    pass

class CluClient:

    def __init__(self, ip: str, port: int, cipher: GrentonCypher, timeout: float = 1) -> None:
        self._addr = (ip, port)
        self._timeout = timeout
        self._local_ip = socket.gethostbyname(socket.gethostname())
        self._cypher = cipher

        self._responses: dict = {}
        self._msg_queue: queue.Queue[tuple[str, threading.Event]] = queue.Queue()

        self._msg_condition = threading.Condition()
        self._msg_sender_thread = threading.Thread(target=self._sender_loop, daemon=True)
        self._msg_sender_thread.start()

    async def send_request_async(self, msg: str):
        event, resp_token = self._appendQueue(msg)

        event.wait()
        resp = self._responses.pop(resp_token)
        
        if isinstance(resp, Exception):
            raise resp
        
        return resp

    def send_request(self, msg: str):
        return asyncio.run(self.send_request_async(msg))
    
    def _appendQueue(self, msg: str):
        with self._msg_condition:
            resp_event = threading.Event()
            resp_token = random.randint(0, 1000000)

            self._msg_queue.put((msg, resp_event, resp_token))
            self._msg_condition.notify_all()

            return resp_event, resp_token
    
    def _sender_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self._timeout)

        while True:
            with self._msg_condition:
                self._msg_condition.wait_for(lambda: not self._msg_queue.empty())
                msg, resp_event, resp_token = self._msg_queue.get()

            payload = self._cypher.encrypt(bytes(msg, "utf-8"))

            try:
                sock.sendto(payload, self._addr)
                
                resp = sock.recvfrom(1024)[0]
                resp = self._cypher.decrypt(resp).decode("utf-8")

                self._responses[resp_token] = resp

            except Exception as e:
                self._responses[resp_token] = e
                
            resp_event.set()

