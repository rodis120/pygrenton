
from dataclasses import dataclass, field

@dataclass
class ModuleConfig:
    serial_number: int
    hw_type: int
    hw_version: int
    fw_type: int
    fw_api_version: int
    fw_verion: str
    status: str

@dataclass
class CLUConfig:
    serial_number: int
    mac: str
    hw_type: int
    hw_version: int
    fw_type: int
    fw_api_version: int
    fw_verion: str
    status: str

    modules: dict[int, ModuleConfig]
