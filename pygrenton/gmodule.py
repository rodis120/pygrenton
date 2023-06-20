
from .config_objects import CLUConfig, ModuleConfig
from .gclu import GCLU
from .gobject import GObject


class IModule:
    _name: str
    _serial_number: int
    
    _hw_type: int
    _hw_version: int
    
    _fw_type: int
    _fw_version: int
    _fw_api_version: int

    def __init__(self, name: str, config: CLUConfig | ModuleConfig) -> None:
        self._name = name
        self._serial_number = config.serial_number
        self._hw_type = config.hw_type
        self._hw_version = config.hw_version
        self._fw_type = config.fw_type
        self._fw_version = config.fw_version
        self._fw_api_version = config.fw_api_version

    @property
    def name(self) -> str:
        return self._name

    @property
    def serial_number(self) -> int:
        return self._serial_number

    @property
    def hw_type(self) -> int:
        return self._hw_type

    @property
    def hw_version(self) -> int:
        return self._hw_version

    @property
    def fw_type(self) -> int:
        return self._fw_type

    @property
    def fw_version(self) -> int:
        return self._fw_version

    @property
    def fw_api_version(self) -> int:
        return self._fw_api_version

class IHasGObjects:
    _gobjects: list[GObject]

    def __init__(self, objects: list[GObject]) -> None:
        self._gobjects = objects

    @property
    def gobjects(self) -> list[GObject]:
        return self._gobjects

    def get_objects_by_type(self, obj_type: int) -> list[GObject]:
        return [obj for obj in self._gobjects if obj.object_type == obj_type]
    
    def get_object_by_id(self, id: str) -> GObject | None:
        for obj in self._gobjects:
            if obj.object_id == id:
                return obj
            
        return None
    
    def get_object_by_name(self, name: str) -> GObject | None:
        for obj in self._gobjects:
            if obj.name == name:
                return obj
            
        return None

class GModule(IModule, IHasGObjects):
    _clu: GCLU
    
    def __init__(self, clu: GCLU, name: str, config: ModuleConfig, gobjects: list[GObject]) -> None:
        self._clu = clu
        IModule.__init__(self, name, config)
        IHasGObjects.__init__(self, gobjects)

    @property
    def clu(self) -> GCLU:
        return self._clu

    