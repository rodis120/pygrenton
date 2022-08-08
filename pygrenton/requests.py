from abc import ABC, abstractmethod
from typing import Any
import random

class Request(ABC):

    def __init__(self, payload: str) -> None:
        chars = "01234567890abcdef"
        self._id = ''.join(random.choices(chars, k=8))
        self._payload = payload

    @abstractmethod
    def parse_response(self, response: str):
        pass

    def id(self) -> str:
        return self._id

    def payload(self) -> str:
        return self._payload

    def create_request(self, ip: str) -> str:
        return "req:" + ip + ':' + self._id + ':' + self._payload

class CheckAlive(Request):

    def __init__(self) -> None:
        super().__init__("checkAlive()")

    def parse_response(self, response: str) -> str:
        spl = response.split(":")
        clu_serial_hex = spl.pop()
        return int(clu_serial_hex, base=16)

class SetRequest(Request):

    def __init__(self, device_id: str, index: int, val: Any) -> None:
        if isinstance(val, str):
            val = '"' + val + '"'
        elif isinstance(val, bool):
            val = str(val).lower()

        payload = "{}:set({},{})".format(device_id, index, val)
        super().__init__(payload)

    def parse_response(self, response: str):
        return None

class GetRequest(Request):

    def __init__(self, device_id: str, index: int) -> None:
        payload = "{}:get({})".format(device_id, index)
        super().__init__(payload)

    def parse_response(self, response: str):
        resp = response.split(":").pop()
        if resp.isdecimal():
            return float(resp)
        elif resp.startswith("\"") and resp.endswith("\""):
            return resp[1:len(resp)]
        elif resp in ["true", "false"]:
            return resp == "true"
        else:
            return None

class ExecuteRequest(Request):

    def __init__(self, device_id: str, intdex: int, *args: Any) -> None:
        params_str = ''.join([(',' + str(i)) for i in args]) if len(args) > 0 else ", 0"
        payload = "{}:execute({}{})".format(device_id, intdex, params_str)
        super().__init__(payload)

    def parse_response(self, response: str):
        resp = response.split(":").pop()
        if resp.isdecimal():
            return float(resp)
        elif resp.startswith("\"") and resp.endswith("\""):
            return resp[1:len(resp)]
        elif resp in ["true", "false"]:
            return resp == "true"
        else:
            return None

