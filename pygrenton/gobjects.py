
from .types import DataType

class GFeature:
    name: str
    index: int
    settable: bool
    gettable: bool
    data_type: DataType
    unit: str

    enum: list
    value_range: tuple[int, int]

    def get(self):
        if not self.gettable:
            return None
        
        #TODO: getting data

    def set(self, value):
        if not self.settable:
            return None
        if self.enum is not None and value not in self.enum:
            return None
        if self.value_range is not None and (value < self.value_range[0] or value > self.value_range[1]):
            return None 
        
        #TODO: setting data

class GMethod:
    name: str
    index: int

    params: list

    return_type: DataType
    unit: str

    def execute(self, **kwargs):
        #TODO: input validation
        #TODO: executing a method
        pass


class GObject:
    _name: str
    _unique_id: str
    _obj_type: int

    _features: list[GFeature]
    _methods: list[GMethod]

    def __init__(self, name: str, id: str, obj_type: int, features: list, methods: list) -> None:
        self._name = name
        self._unique_id = id
        self._obj_type = obj_type
        self._features = features
        self._methods = methods

    def getFeatureByName(self, name: str) -> GFeature | None:
        for feature in self._features:
            if feature.name == name:
                return feature
            
        return None

    def getFeatureByIndex(self, index: int) ->GFeature | None:
        for feature in self._features:
            if feature.index == index:
                return feature
            
        return None

    def getMethodByName(self, name: str) -> GMethod | None:
        for method in self._methods:
            if method.name == name:
                return method
            
        return None

    def getMethodByIndex(self, index: int) ->GMethod | None:
        for method in self._methods:
            if method.index == index:
                return method
            
        return None

class GModule:
    
    objects: list[GObject]

class GCLU:
    pass