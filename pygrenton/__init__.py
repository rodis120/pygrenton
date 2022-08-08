import socket
from .cipher import GrentonCypher
from .requests import Request, CheckAlive

class GrentonApi:

    def __init__(self, ip: str, port: int, key: str, iv: str, timeout: int = 1) -> None:
        self._addr = (ip, port)
        self._timeout = timeout
        self._local_ip = socket.gethostbyname(socket.gethostname())
        self._cypher = GrentonCypher(key, iv)

    def send_request(self, req: Request):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self._timeout)

        payload = self._cypher.encrypt(bytes(req.create_request(self._local_ip), "utf-8"))

        sock.sendto(payload, self._addr)

        resp = sock.recvfrom(1024)[0]
        resp = self._cypher.decrypt(resp).decode("utf-8")
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
