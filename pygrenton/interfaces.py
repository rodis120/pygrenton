
from dataclasses import dataclass, field

from .types import CallType, DataType, ModuleObjectType


@dataclass
class FeatureInterface:
    name: str
    index: int

    get: bool
    set: bool

    data_type: DataType
    unit: str

    enum: dict | None = None
    value_range: tuple[int, int] | None = None

@dataclass
class ParameterInterface:
    name: str
    data_type: DataType
    unit: str

    enum: list | None = None
    value_range: tuple[int, int] | None = None

@dataclass
class MethodInterface:
    name: str
    index: int
    call: CallType

    return_type: DataType
    unit: str | None

    parameters: list[ParameterInterface] = field(default_factory=list)

@dataclass
class CluObjectInterface:
    name: str
    obj_class: int
    version: int

    features: list[FeatureInterface] = field(default_factory=list)
    methods: list[MethodInterface] = field(default_factory=list)

@dataclass
class ModuleObjectInterface:
    name: str
    obj_class: int
    obj_type: ModuleObjectType

    features: list[FeatureInterface] = field(default_factory=list)
    methods: list[MethodInterface] = field(default_factory=list)

@dataclass
class ModuleInterface:
    name: str
    hw_type: int
    fw_type: int
    fw_api_version: int

    objects: dict[int, ModuleObjectInterface] = field(default_factory=dict)

@dataclass
class CluInterface:
    name: str
    hw_type: int
    hw_version: int
    fw_type: int
    fw_api_version: int

    features: list[FeatureInterface] = field(default_factory=list)
    methods: list[MethodInterface] = field(default_factory=list)

    objects: dict[int, CluObjectInterface] = field(default_factory=dict)
