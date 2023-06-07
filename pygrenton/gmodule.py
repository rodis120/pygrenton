
from .gobject import GObject
from .gclu import GCLU

class GModule:
    
    clu: GCLU
    
    name: str
    serial_number: int
    
    hw_type: int
    hw_version: int
    
    fw_type: int
    fw_version: int
    fw_api_version: int
    
    gobjects: list[GObject]
    
    def __init__(self, clu, name, serial_number, hw_type, hw_version, fw_type, fw_version, fw_api_version, gobjects) -> None:
        self.clu = clu
        self.name = name
        self.serial_number = serial_number
        self.hw_type = hw_type
        self.hw_version = hw_version
        self.fw_type = fw_type
        self.fw_version = fw_version
        self.fw_api_version = fw_api_version
        self.gobjects = gobjects
    
    def getObjectsByType(self, obj_type: int) -> list[GObject]:
        return [obj for obj in self.gobjects if obj.obj_type == obj_type]
    
    def getObjectById(self, id: str) -> GObject:
        for obj in self.gobjects:
            if obj.unique_id == id:
                return obj
            
        return None
    
    def getObjectByName(self, name: str) -> GObject:
        for obj in self.gobjects:
            if obj.name == name:
                return obj
            
        return None
    