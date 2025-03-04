import asyncio
import logging
import re
import socket
import threading
from collections.abc import Callable, Iterable
from typing import Any

from .cipher import GrentonCipher
from .client_manager import ClientManager, UpdateContext
from .exceptions import InvalidLuaResponseError
from .utils import (
    generate_id_hex,
    get_host_ip,
)

_LOGGER = logging.getLogger(__name__)

_LUA_RESPONSE_PATTERN = re.compile(r"^resp:\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:[\da-fA-F]+:(.+)$")

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

    def send_lua_request(self, payload: str) -> str|float|bool|None:
        req_id = generate_id_hex()

        # simple lua script that returns data type of the response
        payload = f'req:{self._local_ip}:{req_id}:(function() local res=({payload}) return (type(res) .. ":" .. tostring(res)) end)()'

        resp = self.send_request(payload)
        resp = self._extract_lua_response_payload(resp)

        i = resp.find(":")
        resp_type = resp[:i]
        value = resp[i+1:]

        match resp_type:
            case "number":
                return float(value)
            case "string":
                return value
            case "boolean":
                return value == "true"
            case "nil":
                return None
            case _:
                _LOGGER.debug("Unsupported response type: %s", resp_type)
                return None

    async def send_lua_request_async(self, payload: str) -> str|float|bool|None:
        return await asyncio.to_thread(self.send_lua_request, payload)

    def run_lua_garbage_collector(self) -> None:
        payload = 'collectgarbage("collect")'
        self.send_lua_request(payload)

    def _extract_lua_response_payload(self, response: str) -> str:
        match = _LUA_RESPONSE_PATTERN.match(response)
        if match:
            return match.group(1)

        raise InvalidLuaResponseError(response)
