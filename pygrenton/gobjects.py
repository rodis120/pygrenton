
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
            #TODO: add and rise custom exception
            return None
        
        #TODO: getting data

    def set(self, value):
        if not self.settable:
            #TODO: add and rise custom exception
            return None
        if self.enum is not None and value not in self.enum:
            raise ValueError(f"Value: {value} is not in enum: {self.enum}")
        if self.value_range is not None and (value < self.value_range[0] or value > self.value_range[1]):
            raise ValueError(f"Value: {value} is not in value range: ({self.value_rang[0]} - {self.value_rang[1]})")
        
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
        
    def getFeatures(self) -> list[GFeature]:
        return self._features

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

    def getMethods(self) -> list[GMethod]:
        return self._methods

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
    
    _objects: dict[int, list[GObject]]
    
    #TODO: add constructor
    
    def getObjects(self) -> list[GObject]:
        return [obj for _, obj_list in self._objects.items() for obj in obj_list]
    
    def getObjectsByType(self, type: int) -> list[GObject]:
        if type in self._objects.keys():
            return self._objects[type]
        
        return []
    
    def getObjectById(self, id: str) -> GObject:
        #TODO: decide between creating separate dict or iterating through every object in _objects
        pass
    
    def getObjectByName(self, name: str) -> GObject:
        #TODO: decide between creating separate dict or iterating through every object in _objects
        pass

class GCLU:
    
    #TODO: add constructor
    #TODO: implement(copy it from GrentonApi) request queue
    #TODO: add ways for getting modules and objects
    pass