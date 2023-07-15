import asyncio
import queue
import random
import socket
import threading

from .cipher import GrentonCypher


class CluClient:

    def __init__(self, ip: str, port: int, cipher: GrentonCypher, timeout: float = 1) -> None:
        self._addr = (ip, port)
        self._timeout = timeout
        self._local_ip = socket.gethostbyname(socket.gethostname())
        self._cypher = cipher

        self._responses: dict = {}
        self._msg_queue: queue.Queue[tuple[str, threading.Event, str]] = queue.Queue()

        self._msg_condition = threading.Condition()
        self._msg_sender_thread = threading.Thread(target=self._sender_loop, daemon=True)
        self._msg_sender_thread.start()

    @property
    def clu_ip(self) -> str:
        return self._addr[0]

    @property
    def clu_port(self) -> int:
        return self._addr[1]

    @property
    def client_ip(self) -> str:
        return self._local_ip

    async def send_request_async(self, msg: str) -> str:
        event, resp_token = self._appendQueue(msg)

        event.wait()
        resp = self._responses.pop(resp_token)
        
        if isinstance(resp, Exception):
            raise resp
        
        return resp

    def send_request(self, msg: str):
        return asyncio.get_event_loop().run_until_complete(self.send_request_async(msg))

    async def get_value_async(self, object_id: str, index: int):
        req_id = self._generate_id_hex()
        payload = f"req:{self._local_ip}:{req_id}:{object_id}:get({index})"

        resp = await self.send_request_async(payload)

        resp = resp.split(":").pop()
        if resp.isdecimal():
            return float(resp)
        elif resp.startswith("\"") and resp.endswith("\""):
            return resp[1:len(resp)]
        elif resp in ["true", "false"]:
            return resp == "true"
        else:
            return resp

    def get_value(self, object_id: str, index: int):
        return asyncio.get_event_loop().run_until_complete(self.get_value_async(object_id, index))

    async def set_value_async(self, object_id: str, index: int, value) -> None:
        req_id = self._generate_id_hex()
        payload = f"req:{self._local_ip}:{req_id}:{object_id}:set({index},{value})"

        await self.send_request_async(payload)

    def set_value(self, object_id: str, index: int, value) -> None:
        asyncio.get_event_loop().run_until_complete(self.set_value_async(object_id, index, value))

    async def execute_method_async(self, object_id, index, *args):
        req_id = self._generate_id_hex()
        args_str = ''.join([(',' + str(i)) for i in args]) if len(args) > 0 else ", 0"
        payload = f"req:{self._local_ip}:{req_id}:{object_id}:execute({index}{args_str})"

        resp = await self.send_request_async(payload)

        resp = resp.split(":").pop()
        if resp.isdecimal():
            return float(resp)
        elif resp.startswith("\"") and resp.endswith("\""):
            return resp[1:len(resp)]
        elif resp in ["true", "false"]:
            return resp == "true"
        else:
            return resp

    def execute_method(self, object_id, index, *args):
        return asyncio.get_event_loop().run_until_complete(self.execute_method_async(object_id, index, args))
    
    def _generate_id_hex(self, lenght=8) -> str:
        return ''.join(random.choices("01234567890abcdef", k=lenght))

    def _appendQueue(self, msg: str):
        with self._msg_condition:
            resp_event = threading.Event()
            resp_token = hash((msg, random.random()))

            self._msg_queue.put((msg, resp_event, resp_token))
            self._msg_condition.notify_all()

            return resp_event, resp_token
    
    def _sender_loop(self):
        is_socket_open = False
        sock = None
        
        while True:
            with self._msg_condition:
                self._msg_condition.wait_for(lambda: not self._msg_queue.empty())
                msg, resp_event, resp_token = self._msg_queue.get()

            payload = self._cypher.encrypt(bytes(msg, "utf-8"))

            try:
                if not is_socket_open:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    is_socket_open = True
                
                sock.settimeout(self._timeout)
                sock.sendto(payload, self._addr)
                
                response = sock.recvfrom(1024)[0]
                sock.close()
                
                decrypted = self._cypher.decrypt(response).decode("utf-8")

                self._responses[resp_token] = decrypted
                
                if self._msg_queue.empty():
                    sock.close()
                    is_socket_open = False

            except Exception as e:
                self._responses[resp_token] = e
                
            resp_event.set()

