
import re
import ipaddress
from ipaddress import IPv4Address
from dataclasses import dataclass, field

_NAME_FIELD = re.compile("-- NAME_.*")
_SPLIT_ARGS = re.compile("[ =,\n]+")
_OBJECT_CREATION = re.compile('.*[^"]OBJECT:new\(.*?\)[^"\n]*')

@dataclass
class CLU:
    object_id: str
    ipaddress: IPv4Address

@dataclass
class CLUObject:
    object_id: str
    object_class: int
    
@dataclass
class ModuleObject(CLUObject):
    parent_serial_number: int
    object_index: int

@dataclass
class OMEndpoints:
    this_clu: CLU
    external_clus: list[CLU] = field(default_factory=list)
    
    names: dict[str, str] = field(default_factory=dict)
    
    clu_objects: list[CLUObject] = field(default_factory=list)
    module_objects: dict[int, list[ModuleObject]] = field(default_factory=list)
    
    def getName(self, object_id) -> str:
        if object_id not in self.names.keys():
            return f"UNNAMED_OBJECT_{object_id}"
        
        return self.names[object_id]

def _parse_name(line: str) -> tuple[str, str]:
    spl = re.split(_SPLIT_ARGS, line)[2:]

    name = spl[0]
    object_id = spl[1]

    return object_id, name

def _parse_object_creation(line: str) -> tuple[str, list[str]]:
    obj_id = line.split()[0]
    args = line[line.find("(")+1:line.rfind(")")].split(", ")
    
    return obj_id, args

def _parse_ip_hex(hex_str: str) -> IPv4Address:
    return ipaddress.ip_address(int(hex_str, 16))

def parse_om(file) -> OMEndpoints:
    names: dict[str, str] = {}
    module_objects: dict[int, list[ModuleObject]] = {}
    clu_objects: list[CLUObject] = []
    
    this_clu: CLU = None
    external_clus: list[CLU] = []
            
    for line in file:
        if re.match(_NAME_FIELD, line):
            obj_id, name = _parse_name(line)
            names[obj_id] = name

        elif re.match(_OBJECT_CREATION, line):
            obj_id, args = _parse_object_creation(line)
            argcount = len(args)
            
            if argcount == 2:
                # parse clu object
                clu_objects.append(CLUObject(obj_id, int(args[0])))

            elif argcount == 3 :
                # parse this clu or external clu
                ip_address = _parse_ip_hex(args[1])
                
                if int(args[0]) == 1:
                    external_clus.append(CLU(obj_id, ip_address))
                else:
                    this_clu = CLU(obj_id, ip_address)
                
            elif argcount == 4:
                # parse module object
                obj_class = int(args[0])
                if obj_class == 2:
                    continue
                
                parent_serial_number = int(args[1][3:])
                index = int(args[2])
                
                if parent_serial_number in module_objects.keys():
                    module_objects[parent_serial_number].append(ModuleObject(obj_id, obj_class, parent_serial_number, index))
                else:
                    module_objects[parent_serial_number] = [ModuleObject(obj_id, obj_class, parent_serial_number, index)]

    return OMEndpoints(this_clu, external_clus, names, clu_objects, module_objects)
           