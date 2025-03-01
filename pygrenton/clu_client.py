import asyncio
import logging
import socket
import threading
from collections.abc import Callable, Iterable
from typing import Any

from .cipher import GrentonCipher
from .client_manager import ClientManager, UpdateContext
from .utils import (
    extract_payload,
    generate_id_hex,
    get_host_ip,
)

_LOGGER = logging.getLogger(__name__)

class CluClient:

    def __init__(
        self,
        ip: str,
        port: int,
        cipher: GrentonCipher,
        timeout: float = 1,
        client_refresh_interval: float = 60,
        client_ip: str | None = None,
        client_port: int = 0,
        max_connections: int = 4,
        update_handler_threads: int = 4
    ) -> None:
        self._addr = (ip, port)
        self._timeout = timeout
        self._client_refresh_interval = client_refresh_interval

        if client_ip:
            self._local_ip = client_ip
        else:
            self._local_ip = get_host_ip(ip)

        self._cipher = cipher

        self._request_semaphore = threading.Semaphore(max_connections)

        self._client_manager = ClientManager(cipher, ip, port, client_ip, client_port, update_handler_threads)

    @property
    def clu_ip(self) -> str:
        return self._addr[0]

    @property
    def clu_port(self) -> int:
        return self._addr[1]

    @property
    def client_ip(self) -> str:
        return self._local_ip

    def send_request(self, msg: str, ignore_response: bool = False) -> str:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self._timeout)

        payload = self._cipher.encrypt(msg.encode())

        try:
            with self._request_semaphore:
                sock.sendto(payload, self._addr)
                if not ignore_response:
                    resp, _ = sock.recvfrom(1024)
                    return self._cipher.decrypt(resp).decode()
        finally:
            sock.close()

    async def send_request_async(self, msg: str):
        return await asyncio.to_thread(self.send_request, msg)

    def check_alive(self) -> int:
        return int(self.send_lua_request("checkAlive()"), 16)

    async def check_alive_async(self) -> int:
        return await asyncio.to_thread(self.check_alive)

    def get_value(self, object_id: str, index: int):
        return self.send_lua_request(f"{object_id}:get({index})")

    async def get_value_async(self, object_id: str, index: int):
        return await asyncio.to_thread(self.get_value, object_id, index)

    def set_value(self, object_id: str, index: int, value: Any) -> None:
        self.send_lua_request(f"{object_id}:set({index},{value})")

    async def set_value_async(self, object_id: str, index: int, value: Any) -> None:
        await asyncio.to_thread(self.set_value, object_id, index, value)

    def execute_method(self, object_id: str, index: int, *args: Any):
        args = [f'"{arg}"' if isinstance(arg, str) else str(arg) for arg in args]
        args_str = ",".join(args) if len(args) > 0 else "0"
        return self.send_lua_request(f"{object_id}:execute({index},{args_str})")

    async def execute_method_async(self, object_id: str, index: int, *args: Any):
        return await asyncio.to_thread(self.execute_method, object_id, index, *args)

    def register_value_change_handler(self, object_id: str, index: int|Iterable[int], handler: Callable[[UpdateContext], None]) -> None:
        if isinstance(index, int):
            index = (index,)

        for idx in index:
            self._client_manager.add_update_handler(object_id, idx, handler)

    async def register_value_change_handler_async(self, object_id: str, index: int|Iterable[int], handler: Callable[[UpdateContext], None]) -> None:
        await asyncio.to_thread(self.register_value_change_handler, object_id, index, handler)

    def remove_value_change_handler(self, object_id: str, index: int, handler: Callable[[UpdateContext], None]) -> None:
        self._client_manager.remove_update_handler(object_id, index, handler)

    async def remove_value_change_handler_async(self, object_id: str, index: int, handler: Callable[[UpdateContext], None]) -> None:
        await asyncio.to_thread(self.remove_value_change_handler, object_id, index, handler)

    def send_lua_request(self, payload: str, ignore_response: bool = False, ignore_type: bool = False) -> str|float|bool:
        req_id = generate_id_hex()

        if not (ignore_type or ignore_response):
            # basically remote code execution
            payload = f'(load("result = {payload} return (type(result) .. \\":\\" .. tostring(result))")())'

        payload = f"req:{self._local_ip}:{req_id}:{payload}"

        resp = self.send_request(payload, ignore_response)

        if ignore_response:
            return None

        resp = extract_payload(resp)

        if ignore_type:
            return resp

        i = resp.find(":")

        resp_type = resp[:i]
        value = resp[i+1:]

        if resp_type == "number":
            return float(value)
        if resp_type == "string":
            return value
        if resp_type == "boolean":
            return value == "true"
        return None

    async def send_lua_request_async(self, payload: str, ignore_response: bool = False, ignore_type: bool = False) -> str|float|bool:
        return await asyncio.to_thread(self.send_lua_request, payload, ignore_response, ignore_type)

    def run_lua_garbage_collector(self) -> None:
        payload = 'collectgarbage("collect")'
        self.send_lua_request(payload, ignore_response=True, ignore_type=True)

