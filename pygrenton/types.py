
from enum import Enum


class CallType(Enum):
    EXECUTE = "execute"
    GET = "get"
    SET = "set"

class DataType(Enum):
    VOID = "void"
    NUMBER = "num"
    INTEGER = "int"
    ENUM = "enum"
    STRING = "str"
    TABLE = "table"
    TIMESTAMP = "timestamp"
    CONFIRMATION = "confirmation"
    NONE = ""

class ModuleObjectType(Enum):
    NONE = "none"
    OUT = "out"
    IN = "in"