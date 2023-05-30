
from dataclasses import dataclass
from .types import CallType, DataType, ModuleObjectType

@dataclass
class FeatureInterface:
    name: str
    index: int

    get: bool
    set: bool

    data_type: DataType
    unit: str

    enum: list = None
    value_range: tuple[int, int] = None

@dataclass
class ParameterInterface:
    name: str
    data_type: DataType
    unit: str

    enum: list = None
    value_range: tuple[int, int] = None

@dataclass
class MethodInterface:
    name: str
    index: int
    call: CallType

    parameters: list[ParameterInterface]

    return_type: DataType
    unit: str

@dataclass
class CluObjectInterface:
    name: str
    obj_class: int
    version: int

    features: list[FeatureInterface]
    methods: list[MethodInterface]

@dataclass
class ModuleObjectInterface:
    name: str
    obj_class: int
    type: ModuleObjectType

    features: list[FeatureInterface]
    methods: list[MethodInterface]

@dataclass
class ModuleInterface:
    name: str
    hw_type: int
    fw_type: int
    fw_api_version: int

    objects: list[ModuleObjectInterface]

@dataclass
class CluInterface:
    name: str
    hw_type: int
    hw_version: int
    fw_type: int
    fw_api_version: int

    features: list[FeatureInterface]
    methods: list[MethodInterface]

    objects: dict[str, int]