
from gobject import GObject
from gclu import GCLU

class GModule:
    
    #TODO: add data about module eg. name, hwType, version etc.
    
    clu: GCLU
    gobjects: list[GObject]
    
    def __init__(self) -> None:
        #TODO: just do it.
        pass
    
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
    