
from datetime import datetime
from enum import Enum


class CallType(Enum):
    EXECUTE = "execute"
    GET = "get"
    SET = "set"

class DataType(Enum):
    #TODO: make data types more generic
    VOID = "void"
    NUMBER = "num"
    INTEGER = "int"
    ENUM = "enum"
    STRING = "str"
    TABLE = "table"
    TIMESTAMP = "timestamp"
    CONFIRMATION = "confirmation"
    NONE = ""
    
    def convert_value(self, var):
        if self.value == DataType.NUMBER:
            return float(var)
        elif self.value == DataType.INTEGER:
            return int(var)
        elif self.value == DataType.TIMESTAMP:
            return datetime.fromtimestamp(float(var))
        else:
            return var
class ModuleObjectType(Enum):
    NONE = "none"
    OUT = "out"
    IN = "in"