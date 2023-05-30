
from enum import Enum

class CallType(Enum):
    EXECUTE = "execute"
    GET = "get"
    SET = "set"

class DataType(Enum):
    VOID = "void"
    NUMBER = "num"
    ENUM = "enum"
    STRING = "str"

class ModuleObjectType(Enum):
    OUT = "out"
    IN = "in"