
from .types import DataType, CallType
from .gclu import GCLU

class GFeature:
    clu: GCLU
    name: str
    index: int
    settable: bool
    gettable: bool
    data_type: DataType
    unit: str

    enum: list
    value_range: tuple[int, int]
    
    def __init__(self, clu, name, index, settable, gettable, data_type, unit, enum=None, value_range=None) -> None:
        self.clu = clu
        self.name = name
        self.index = index
        self.settable = settable
        self.gettable = gettable
        self.data_type = data_type
        self.unit = unit
        self.enum = enum
        self.value_range = value_range

    def getValue(self):
        if not self.gettable:
            #TODO: add and rise custom exception
            return None
        
        #TODO: getting data

    def setValue(self, value):
        if not self.settable:
            #TODO: add and rise custom exception
            return None
        if self.enum is not None and value not in self.enum:
            raise ValueError(f"Value: {value} is not in enum: {self.enum}")
        if self.value_range is not None and (value < self.value_range[0] or value > self.value_range[1]):
            raise ValueError(f"Value: {value} is not in value range: ({self.value_range[0]} - {self.value_range[1]})")
        
        #TODO: setting data

class GMethod:
    clu: GCLU
    name: str
    index: int
    call_type: CallType

    #TODO: implement parameters
    params: list

    return_type: DataType
    unit: str
    
    def __init__(self, clu, name, index, call_type, params, return_type, unit) -> None:
        self.clu = clu
        self.name = name
        self.index = index
        self.call_type = call_type
        self.params = params
        self.return_type = return_type
        self.unit = unit

    def execute(self, **kwargs):
        #TODO: input validation
        #TODO: executing a method
        pass

class GObject:
    clu: GCLU
    name: str
    id: str
    obj_type: int

    features: list[GFeature]
    methods: list[GMethod]
    
    def __init__(self, clu, name, id, obj_type, features, methods) -> None:
        self.clu = clu
        self.name = name
        self.id = id
        self.obj_type = obj_type
        self.features = features
        self.methods = methods

    def getFeatureByName(self, name: str) -> GFeature | None:
        for feature in self.features:
            if feature.name == name:
                return feature
            
        return None

    def getFeatureByIndex(self, index: int) -> GFeature | None:
        for feature in self.features:
            if feature.index == index:
                return feature
            
        return None

    def getMethodByName(self, name: str) -> GMethod | None:
        for method in self.methods:
            if method.name == name:
                return method
            
        return None

    def getMethodByIndex(self, index: int) -> GMethod | None:
        for method in self.methods:
            if method.index == index:
                return method
            
        return None
    
    def getValue(self, index: int):
        pass
    
    def setValue(self, index: int, value):
        pass
    
    def execute(self, index: int, **kwargs):
        pass
