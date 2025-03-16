"""Grenton om.lua file parser."""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from io import TextIOWrapper
from ipaddress import IPv4Address, ip_address
from itertools import chain
from pathlib import Path

# Reminder: capturing group names must be unique
_TOKEN_SPECIFICATION = [
    ("OBJECT_NAME", r"-- NAME_\w+ (?P<NAME>\S+)=(?P<ID>\S+)"),
    ("OBJECT", r"(?P<OBJ_ID>\S+) = OBJECT:new\((?P<ARGS>)\)"),
]
_TOKEN_REGEX = re.compile("|".join("(?P<{}>{})".format(*pair) for pair in _TOKEN_SPECIFICATION))
_SPLIT_ARGS_PATTERN = re.compile(r"(\"(?:\\\"|[^\"])*\")|([^,\s]+)")

@dataclass
class CLUObject:
    object_id: str
    object_class: int

@dataclass
class CLU(CLUObject):
    clu_ip: IPv4Address
    clu_type: str

@dataclass
class Module(CLUObject):
    serial_number: int
    module_type: int

@dataclass
class ModuleObject(CLUObject):
    module: Module
    object_index: int

@dataclass
class _TemporaryModuleObject(CLUObject):
    module_id: str
    object_index: int

@dataclass
class _ObjectName:
    object_id: str
    name: str

@dataclass
class _Label:
    label: str

@dataclass
class OMEndpoints:
    local_clu: CLU
    remote_clus: list[CLU]

    module_objects: dict[int, list[ModuleObject]]
    clu_objects: list[CLUObject]

    names: dict[str, str]

    def get_name(self, object_id: str) -> str:
        if object_id not in self.names:
            return f"UNNAMED_OBJECT_{object_id}"

        return self.names[object_id]

def _parse_args(args: str) -> list[int|str|bool|_Label|None]:
    out = []
    for val in {m[0] or m[1] for m in re.finditer(_SPLIT_ARGS_PATTERN, args)}:
        if val.isdecimal():
            out.append(int(val))
        elif val.startswith("0x"):
            out.append(int(val, base=16))
        elif val.startswith('"') and val.endswith('"'):
            out.append(val[1:-1])
        elif val in ("true", "false"):
            out.append(val == "true")
        elif val == "nil":
            out.append(None)
        else:
            out.append(_Label(val))
    return out

def _parse_object(object_id: str, args: list) -> CLUObject:
    match args[0]:
        case 0 | 1:
            return CLU(object_id, args[0], ip_address(args[1]))
        case 2:
            return Module(object_id, args[0], args[1], args[2])
        case _:
            if isinstance(args[1], _Label):
                return _TemporaryModuleObject(object_id, args[0], args[1].label, args[2])
            return CLUObject(object_id, args[0], args[1], args[2])

def _tokenize(file: TextIOWrapper) -> Iterator[_ObjectName | CLUObject]:
    for mo in chain.from_iterable({re.finditer(_TOKEN_REGEX, line) for line in file}):
        match mo.lastgroup:
            case "OBJECT_NAME":
                name = mo.group("NAME")
                object_id = mo.group("ID")
                yield _ObjectName(object_id, name)

            case "OBJECT":
                object_id = mo.group("OBJ_ID")
                args = _parse_args(mo.group("ARGS"))
                yield _parse_object(object_id, args)

def parse_om(filepath: Path) -> OMEndpoints:
    local_clu: CLU = None
    remote_clus: list[CLU] = []
    modules: dict[str, Module] = {}
    module_objects: dict[str, ModuleObject] = {}
    clu_objects: dict[str, CLUObject] = {}
    names: dict[str, str] = {}

    with filepath.open(filepath, mode="r") as file:
        for token in _tokenize(file):
            if isinstance(token, _ObjectName):
                names[token.object_id] = token.name
            elif isinstance(token, CLU):
                if token.object_class == 0:
                    local_clu = token
                else:
                    remote_clus.append(token)
            elif isinstance(token, Module):
                modules[token.object_id] = token
            elif isinstance(token, _TemporaryModuleObject):
                module_objects[token.object_id] = ModuleObject(token.object_id, token.object_class, modules[token.module_id], token.object_index)
            elif isinstance(token, CLUObject):
                clu_objects[token.object_id] = token

    return OMEndpoints(local_clu, remote_clus, module_objects, clu_objects, names)
