
import re

_NAME_FIELD = re.compile("-- NAME_.*")
_MODULE_FIELD = re.compile("mm_\d{9} = OBJECT:new([^,]*,[^,\n]*){3}\) --.*") #TODO: delete it
_IO_MODULE_FIELD = re.compile("[A-Z]{3}\d{4}.*OBJECT:new([^,]*,[^,\n]*){3}\)")
_OBJECT_FIELD = re.compile("[A-Z]{3}\d{4}.*OBJECT:new([^,]*,[^,\n]*){1}\)")
_EXTRACT_BRACKET = re.compile("(?<=\().*(?=\))")
_EXTRACT_COMMENT = re.compile("(?<=-- ).*")
_EXTRACT_NUMBER = re.compile("\d*")
_SPLIT_ARGS = re.compile("[ =,]*")

def _parse_name(line: str) -> tuple[str, str]:
    spl = re.split(_SPLIT_ARGS, line)[-2:]

    name = spl[0]
    object_id = spl[1]

    return object_id, name

#TODO: delete this too
def _parse_module(line: str) -> tuple[int, int, int, int]:
    bracket = re.search(_EXTRACT_BRACKET, line).string
    args1 = re.split(_SPLIT_ARGS, bracket)

    comment = re.search(_EXTRACT_COMMENT, line).string
    args2 = comment.split(" ")

    sn = int(args2[0])
    hw_type = int(args1[2], 16)
    fw_type = int(args2[1])
    fw_api_version = int(args2[2])

    return sn, hw_type, fw_type, fw_api_version

def _parse_io_module(line: str) -> tuple[str, int, int]:
    bracket = re.search(_EXTRACT_BRACKET, line).string
    args = re.split(_SPLIT_ARGS, bracket)

    object_class = int(args[0])
    module_sn = int(re.search(_EXTRACT_NUMBER, args[1]).string)
    object_id = args[3][1:-1]

    return object_id, object_class, module_sn

def _parse_object(line: str) -> tuple[str, int]:
    bracket = re.search(_EXTRACT_BRACKET, line).string
    args = re.split(_SPLIT_ARGS, bracket)

    object_class = int(args[0])
    object_id = args[1][1:-1]

    return object_id, object_class

def parse_om(file):
    names: dict[str, str] = {}
    io_modules: dict[int, list[tuple[str, int, int]]] = {}
    objects: list[tuple[str, int]] = []

    for line in file:
        if re.match(_NAME_FIELD, line):
            obj_id, name = _parse_name(line)
            names[obj_id] = name

        elif re.match(_IO_MODULE_FIELD, line):
            io_mod = _parse_io_module(line)
            sn = io_mod[2]
            
            if io_modules[sn] is not None:
                io_modules[sn].append(io_mod)
            else:
                io_modules[sn] = [io_mod]
        
        elif re.match(_OBJECT_FIELD, line):
            obj = _parse_object(line)
            objects.append(obj)

    return names, io_modules, objects

                