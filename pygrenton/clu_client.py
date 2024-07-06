import asyncio
import random
import socket
import threading
from dataclasses import dataclass
from collections.abc import Callable
from typing import Any

from .cipher import GrentonCipher


def _get_host_ip(clu_ip: str) -> str:
    _, _, ips = socket.gethostbyname_ex(socket.gethostname())

    for ip in ips:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((ip, 0))
        
        try:
            sock.sendto(b"", (clu_ip, 1234))
            return ip
        except:
            pass
        
    #TODO: throw exception when no ip is found
    return ""

def _find_n_character(string: str, char: str, n: int) -> int:
    count = 0
    for index, c in enumerate(string):
        if c == char:
            count += 1
            if count == n:
                return index
            
    return -1

def _extract_payload(resp: str) -> str:
    index = _find_n_character(resp, ':', 3)
    if index == -1:
        return resp
         
    return resp[index + 1:]
        
def _generate_id_hex(lenght=8) -> str:
        return ''.join(random.choices("01234567890abcdef", k=lenght))

def _parse_list(msg: str, start: int = 0) -> tuple[int, list]:
    values = []
    i = start
    prev_i = start
    quote = False
    
    def convert_type(data: str):
        data = data.strip()
        if data.startswith('"') and data.endswith('"'):
            return data[1:-1]
        elif data == "true":
            return True
        elif data == "false":
            return False
        elif data == "nil":
            return None
        
        return float(data)
    
    def append_if_not_empty(m: str):
        if m.strip() != "":
            values.append(convert_type(m))
    
    length = len(msg)
    while i < length:
        c = msg[i]
        if c == ',' and not quote:
            append_if_not_empty(msg[prev_i:i])
            prev_i = i+1 
        elif c == '"':
            quote = not quote
        elif c == '{' and not quote:
            i, sub_list = _parse_list(msg, i+1)
            prev_i = i + 1
            values.append(sub_list)   
        elif c == '}' and not quote:
            append_if_not_empty(msg[prev_i:i])
            return i, values
        
        i += 1
    
    values.append(convert_type(msg[prev_i:]))
    return i-1, values      
 
def _parse_update_message(msg: str) -> tuple[int, list]:
    index = _find_n_character(msg, ':', 4)
    msg = msg[index + 1:]
    
    index = msg.find(':')
    client_id = int(msg[:index])
    
    msg = msg[index + 2:-1]
    _, values = _parse_list(msg)
    
    return client_id, values

def _gen_client_id(object_id: str) -> int:
    acc = 0
    for c in object_id.encode():
        acc <<= 4
        acc ^= c    
        
    return acc

@dataclass
class UpdateContext:
    object_id: str
    index: int
    value: Any

class CluClient:

    def __init__(
        self,
        ip: str,
        port: int,
        cipher: GrentonCipher,
        timeout: float = 1,
        registration_update_interval: float = 60,
        client_ip: str | None = None,
        client_port: int = 0,
        max_connections: int = 6
    ) -> None:
        self._addr = (ip, port)
        self._timeout = timeout
        self._registration_update_interval = registration_update_interval
        
        if client_ip:
            self._local_ip = client_ip
        else:
            self._local_ip = _get_host_ip(ip)
            
        self._cipher = cipher
        
        self._request_semaphore = threading.Semaphore(max_connections)

        self._client_id_map: dict[int, str] = {}
        self._handler_map: dict[tuple[str, int], Callable[[str, int, Any], None]] = {}
        self._feature_index_map: dict[str, list[int]] = {}
        self._states_map: dict[tuple[str, int], Any] = {}
        
        self._update_receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._update_receiver_socket.bind((self._local_ip, client_port))
        self._update_receiver_port = self._update_receiver_socket.getsockname()[1]
        self._update_receiver_thread = threading.Thread(target=self._update_receiver, daemon=True)
        self._update_receiver_thread.start()
        
        self._client_registration_payloads: dict[str, str] = {}
        self._client_registration_lock = threading.Lock()
        self._client_registration_thread = threading.Thread(target=self._client_registration, daemon=True)
        # self._client_registration_thread.start()

    @property
    def clu_ip(self) -> str:
        return self._addr[0]

    @property
    def clu_port(self) -> int:
        return self._addr[1]

    @property
    def client_ip(self) -> str:
        return self._local_ip
    
    def start_client_registration(self):
        self._client_registration_thread.start()

    def send_request(self, msg: str) -> str:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self._timeout)
        
        payload = self._cipher.encrypt(msg.encode())
        
        try:
            with self._request_semaphore:
                sock.sendto(payload, self._addr)
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
    
    def register_value_change_handler(self, object_id: str, index: int, handler: Callable[[UpdateContext], None]) -> None:
        with self._client_registration_lock:
            client_id = _gen_client_id(object_id)
            self._client_id_map[client_id] = object_id
            
            if object_id in self._feature_index_map.keys():
                self._feature_index_map[object_id].append(index)
            else:
                self._feature_index_map[object_id] = [index]
            
            self._handler_map[(object_id, index)] = handler
            
            payload = self._create_registration_payload(object_id)
            self._client_registration_payloads[object_id] = payload
            
            # resp = self.send_request(payload)
            # self._handle_update_message(resp)
        
    def remove_value_change_handler(self, object_id: str, index: int) -> None:
        with self._client_registration_lock:
            self._client_id_map.pop(_gen_client_id(object_id))
            
            index_map = self._feature_index_map[object_id]
            index_map.remove(index)
            if len(index_map) == 0:
                self._feature_index_map.pop(object_id)
                self._client_registration_payloads.pop(object_id)
            else:
                payload = self._create_registration_payload(object_id)
                self._client_registration_payloads[object_id] = payload
            
            self._handler_map.pop((object_id, index))

    def _send_lua_request(self, payload) -> str:
        req_id = _generate_id_hex()
        payload = f'req:{self._local_ip}:{req_id}:(load("result = {payload} return (type(result) .. \\\":\\\" .. tostring(result))")())' # basically remote code execution
    
        resp = self.send_request(payload)
        resp = _extract_payload(resp)
        
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

    def _create_registration_payload(self, object_id: str) -> str:
        client_id =_gen_client_id(object_id)
        items = [f"{{{object_id},{i}}}" for i in self._feature_index_map[object_id]]
        port = self._update_receiver_port
        payload = f"req:{self._local_ip}:{_generate_id_hex()}:SYSTEM:clientRegister(\"{self._local_ip}\",{port},{client_id},{{{','.join(items)}}})"
        return payload
    
    def _client_registration(self) -> None:
        
        tasks = set()
        def done_callback(resp_task: asyncio.Task[str]) -> None:
            with self._client_registration_lock:
                self._handle_update_message(resp_task.result())
            tasks.discard(resp_task)
        
        async def main():
            while True:
                # TODO: I'm not sure if that Lock is a good idea
                with self._client_registration_lock:
                    for payload in self._client_registration_payloads.values():
                        task = asyncio.create_task(self.send_request_async(payload))
                        tasks.add(task)
                        task.add_done_callback(done_callback)
                
                await asyncio.sleep(self._registration_update_interval)
                
        asyncio.run(main())
        
    def _update_receiver(self) -> None:
        
        while True:
            try:
                encrypted, _ = self._update_receiver_socket.recvfrom(1024)
                decrypted = self._cipher.decrypt(encrypted).decode("utf-8")
            except:
                continue
            
            with self._client_registration_lock:
                self._handle_update_message(decrypted)
            
    def _handle_update_message(self, message: str):
        
        client_id, values = _parse_update_message(message)
        object_id = self._client_id_map.get(client_id, None)
        if object_id == None:
            return
        
        index_map = self._feature_index_map[object_id]
        
        for i, v in enumerate(values):
            index = index_map[i]
            
            key = (object_id, index)
            
            prev_state = self._states_map.get(key, None)
            if prev_state != v:
                self._states_map[key] = v
                handler = self._handler_map[key]
                
                threading.Thread(target=handler, args=(UpdateContext(object_id, index, v),)).start()
