
import socket
import random

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

def parse_list(msg: str, start: int = 0) -> tuple[int, list]:
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
            i, sub_list = parse_list(msg, i+1)
            prev_i = i + 1
            values.append(sub_list)   
        elif c == '}' and not quote:
            append_if_not_empty(msg[prev_i:i])
            return i, values
        
        i += 1
    
    values.append(convert_type(msg[prev_i:]))
    return i-1, values