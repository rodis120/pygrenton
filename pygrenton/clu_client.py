import asyncio
import socket
import threading
import time
from dataclasses import dataclass, field
from collections.abc import Callable
from typing import Any

from .cipher import GrentonCipher     
from .utils import (
    find_n_character,
    parse_list,
    get_host_ip,
    generate_id_hex,
    extract_payload
)

def _parse_update_message(msg: str) -> tuple[int, list]:
    index = find_n_character(msg, ':', 4)
    msg = msg[index + 1:]
    
    index = msg.find(':')
    client_id = int(msg[:index])
    
    msg = msg[index + 2:-1]
    _, values = parse_list(msg)
    
    return client_id, values

@dataclass
class UpdateContext:
    object_id: str
    index: int
    value: Any
    
@dataclass(eq=True, unsafe_hash=True)
class FeatureEntry:
    object_id: str
    index: int
    
@dataclass
class ClientPage:
    client_id: int
    features: list[FeatureEntry] = field(default_factory=list)
    modified: bool = False
    last_mod: float = field(default_factory=time.time)
    states: list[Any] = field(default_factory=list)
    
    def create_payload(self, client_ip, client_port) -> str:
        features_str = '{' + ','.join([f"{{{fe.object_id},{fe.index}}}" for fe in self.features]) + '}'
        return f'SYSTEM:clientRegister("{client_ip}",{client_port},{self.client_id},{features_str})'
    
    def __hash__(self) -> int:
        return hash(self.client_id)

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
        page_size: int = 16
    ) -> None:
        self._addr = (ip, port)
        self._timeout = timeout
        self._client_refresh_interval = client_refresh_interval
        
        if client_ip:
            self._local_ip = client_ip
        else:
            self._local_ip = get_host_ip(ip)
            
        self._cipher = cipher
        self._page_size = page_size
        
        self._request_semaphore = threading.Semaphore(max_connections)

        self._client_pages_index: dict[FeatureEntry, ClientPage] = {}
        self._client_pages: dict[int, ClientPage] = {}
        self._free_client_pages: set[ClientPage] = set()
        self._handler_map: dict[FeatureEntry, Callable[[UpdateContext], None]] = {}
        
        self._update_receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._update_receiver_socket.bind((self._local_ip, client_port))
        self._update_receiver_port = self._update_receiver_socket.getsockname()[1]
        self._update_receiver_thread = threading.Thread(target=self._update_receiver, daemon=True)
        self._update_receiver_thread.start()
        
        self._client_registration_lock = threading.Lock()
        self._client_refresh_thread = threading.Thread(target=self._refresh_client_pages, daemon=True)
        self._client_refresh_thread.start()
        
    @property
    def clu_ip(self) -> str:
        return self._addr[0]

    @property
    def clu_port(self) -> int:
        return self._addr[1]

    @property
    def client_ip(self) -> str:
        return self._local_ip

    def send_request(self, msg: str, ignore_response: bool = True) -> str:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self._timeout)
        
        payload = self._cipher.encrypt(msg.encode())
        
        try:
            with self._request_semaphore:
                sock.sendto(payload, self._addr)
                if not ignore_response:
                    resp, _ = sock.recvfrom(1024)
                    return self._cipher.decrypt(resp).decode()
                
        except Exception as e:
            raise e
        finally:
            sock.close()

    async def send_request_async(self, msg: str):
        return await asyncio.to_thread(self.send_request, msg)
    
    def check_alive(self) -> int:
        return int(self._send_lua_request("checkAlive()"), 16)
    
    async def check_alive_async(self) -> int:
        return await asyncio.to_thread(self.check_alive)

    def get_value(self, object_id: str, index: int):
        return self._send_lua_request(f"{object_id}:get({index})")

    async def get_value_async(self, object_id: str, index: int):
        return await asyncio.to_thread(self.get_value, object_id, index)

    def set_value(self, object_id: str, index: int, value) -> None:
        self._send_lua_request(f"{object_id}:set({index},{value})")

    async def set_value_async(self, object_id: str, index: int, value) -> None:
        await asyncio.to_thread(self.set_value, object_id, index, value)

    def execute_method(self, object_id, index, *args):
        args = list(map(lambda arg: f'"{arg}"' if isinstance(arg, str) else str(arg), args))
        args_str = ','.join([i for i in args]) if len(args) > 0 else '0'
        return self._send_lua_request(f"{object_id}:execute({index},{args_str})")
    
    async def execute_method_async(self, object_id, index, *args):
        return await asyncio.to_thread(self.execute_method, object_id, index, *args)
    
    # Client registration section
    def register_value_change_handler(self, object_id: str, index: int, handler: Callable[[UpdateContext], None]) -> None:
        with self._client_registration_lock:
            fentry = FeatureEntry(object_id, index)
            if fentry in self._handler_map.keys():
                self._handler_map[fentry] = handler
                return
            
            self._handler_map[fentry] = handler
            
            page: ClientPage = None
            if len(self._free_client_pages) > 0:
                page = self._free_client_pages.pop()
                if len(page.features) < self._page_size - 1:
                    self._free_client_pages.add(page)
                page.modified = True
                
            else:
                page = self._create_new_page()
                
            page.features.append(fentry)
            self._client_pages_index[fentry] = page
            
            self._refresh_page(page)
            
    async def register_value_change_handler_async(self, object_id: str, index: int, handler: Callable[[UpdateContext], None]) -> None:
        await asyncio.to_thread(self.register_value_change_handler, object_id, index, handler)
        
    def remove_value_change_handler(self, object_id: str, index: int) -> None:
        with self._client_registration_lock:
            fentry = FeatureEntry(object_id, index)
            del self._handler_map[fentry]
            
            page = self._client_pages_index.pop(fentry)
            page.features.remove(fentry)
            page.modified = True
            
            if len(page.features) == 0:
                self._free_client_pages.remove(page)
                self._client_pages.pop(page.client_id)
            else:
                self._free_client_pages.add(page)
                
            self._refresh_page(page)
            
    async def remove_value_change_handler_async(self, object_id: str, index: int) -> None:
        await asyncio.to_thread(self.remove_value_change_handler(object_id, index))
        
    def _send_lua_request(self, payload: str, ignore_response: bool = False, ignore_type: bool = False) -> str:
        req_id = generate_id_hex()
        
        if not (ignore_type or ignore_response):
            # basically remote code execution
            payload = f'(load("result = {payload} return (type(result) .. \\\":\\\" .. tostring(result))")())'
            
        payload = f'req:{self._local_ip}:{req_id}:{payload}' 
    
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
        elif resp_type == "string":
            return value
        elif resp_type == "boolean":
            return value == "true"
        else:
            return None
        
    def _refresh_client_pages(self):
        while True:
            with self._client_registration_lock:
                try:
                    for page in self._client_pages.values():
                        self._refresh_page(page)
                except Exception as e:
                    print(e)
            
            time.sleep(self._client_refresh_interval)
        
    def _update_receiver(self) -> None:
        
        while True:
            try:
                encrypted, _ = self._update_receiver_socket.recvfrom(1024)
                decrypted = self._cipher.decrypt(encrypted).decode("utf-8")
            except:
                continue
            
            msg_time = time.time()
            with self._client_registration_lock:
                self._handle_update_message(decrypted, msg_time)
            
    def _handle_update_message(self, message: str, message_timestamp: float):
        client_id, values = _parse_update_message(message)
        page = self._client_pages.get(client_id, None)
        if page == None:
            return
        
        if page.modified:
            page.states = values
            page.modified = False
            
            if page.last_mod > message_timestamp:
                return
            
            for entry, value in zip(page.features, values):
                self._procces_update(entry, value)
                
        else:
            for entry, _, new_value in filter(lambda x: x[1] != x[2], zip(page.features, page.states, values)):
                self._procces_update(entry, new_value)
            page.states = values
                
    def _procces_update(self, entry: FeatureEntry, value: Any):
        handler = self._handler_map[entry]
        threading.Thread(target=handler, args=(UpdateContext(entry.object_id, entry.index, value),)).start()
                
    def _create_new_page(self) -> ClientPage:
        used_ids = self._client_pages.keys()
        
        client_id = 1
        while client_id in used_ids:
            client_id += 1
            
        page = ClientPage(client_id)
        
        self._client_pages[client_id] = page
        self._free_client_pages.add(page)
        
        return page
    
    def _register_page(self, page: ClientPage) -> None:
        resp = self._send_lua_request(page.create_payload(self._local_ip, self._update_receiver_port), ignore_type=True)
        i = resp.find(':')
        self._handle_update_message(resp[i+1:], time.time())
    
    def _unregister_page(self, page: ClientPage) -> None:
        self._send_lua_request(f'SYSTEM:clientDestroy("{self._local_ip}",{self._update_receiver_port},{page.client_id})', ignore_response=True)
        
    def _refresh_page(self, page: ClientPage) -> None:
        self._unregister_page(page)
        self._register_page(page)
        page.last_mod = time.time()
        