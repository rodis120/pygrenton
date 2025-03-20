
import random
import re
import socket
from typing import Any

#TODO: guess what happens when " is a character in a string
_LIST_PARSE_PATTERN = re.compile(r"(?P<STR>\"[^\"]*?\")|(?P<NUM>\d+(?:\.\d+)?)|(?P<BOOL>true|false)|(?P<NIL>nil)")

def get_host_ip(clu_ip: str) -> str:
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

def gen_session_id(bits: int=32) -> str:
    return hex(random.randint(0, 2**bits))[2:]  # noqa: S311

def parse_list(text: str) -> list[Any]:
    out = []
    for m in re.finditer(_LIST_PARSE_PATTERN, text):
        match m.lastgroup:
            case "STR":
                out.append(m.string[1:-1])
            case "NUM":
                out.append(float(m.string))
            case "BOOL":
                out.append(m.string == "true")
            case "NIL":
                out.append(None)

    return out
