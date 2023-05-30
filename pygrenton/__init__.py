import socket
import threading
import time
from .cipher import GrentonCypher
from .requests import Request, CheckAlive

class GrentonApi:

    def __init__(self, ip: str, port: int, key: str, iv: str, timeout: float = 1) -> None:
        self._addr = (ip, port)
        self._timeout = timeout
        self._local_ip = socket.gethostbyname(socket.gethostname())
        self._cypher = GrentonCypher(key, iv)

        self._responses: dict = {}
        self._msg_queue: list[tuple[Request, threading.Condition]] = []

        self._msg_condition = threading.Condition()
        self._msg_sender_thread = threading.Thread(target=self._sender_loop, daemon=True)
        self._msg_sender_thread.start()

    def send_request(self, req: Request):
        cv = self._appendQueue(req)

        with cv:
            cv.wait(self._timeout)
            resp = self._responses[req._id]
            if resp is None:
                raise TimeoutError
            
            return req.parse_response(resp)

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
            resp_cv = threading.Condition()

            self._msg_queue += (req, resp_cv)
            self._msg_condition.notify_all()

            return resp_cv
    
    def _sender_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self._timeout)

        while True:
            with self._msg_condition:
                self._msg_condition.wait_for(lambda: not len(self._msg_queue) == 0)
                req, resp_cv = self._msg_queue.pop(0)

            payload = self._cypher.encrypt(bytes(req.create_request(self._local_ip), "utf-8"))

            sock.sendto(payload, self._addr)

            try:
                resp = sock.recvfrom(1024)[0]
                resp = self._cypher.decrypt(resp).decode("utf-8")

                self._responses[req._id] = resp
                resp_cv.notify_all()

            except:
                pass

