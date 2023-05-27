
from dataclasses import dataclass, field

@dataclass
class Module:
    serial_number: int
    hw_type: int
    hw_version: int
    fw_type: int
    fw_api_version: int
    fw_verion: str
    status: str

    io_modules: list = field(default_factory=lambda : [])

@dataclass
class GObject:
    unique_id: str
    obj_class: int
    type: str
    name: str

    features: list = field(default_factory=lambda : [])
    methods: list = field(default_factory=lambda : [])

@dataclass
class IO_Module(GObject):
    module: Module

@dataclass
class CLU_Module:
    serial_number: int
    mac: str
    hw_type: int
    hw_version: int
    fw_type: int
    fw_api_version: int
    fw_verion: str
    status: str

    tf_bus_devices: list[Module] = field(default_factory=lambda : [])
    zwave_devices: list[Module] = field(default_factory=lambda : [])
    objects: list = field(default_factory=lambda : [])
    
    
