
import asyncio

from .clu_client import CluClient
from .gfeature import GFeature
from .gmethod import GMethod
from .interfaces import CluInterface, CluObjectInterface, ModuleObjectInterface
from .types import ModuleObjectType


class GObject:
    _clu_client: CluClient
    _name: str
    _object_id: str
    _version: int | None
    _obj_type: ModuleObjectType | None

    _features: list[GFeature]
    _methods: list[GMethod]
    
    def __init__(self, clu_client: CluClient, name: str, object_id: str, interface: CluInterface | CluObjectInterface | ModuleObjectInterface) -> None:
        self._clu_client = clu_client
        self._name = name
        self._object_id = object_id

        if isinstance(interface, CluObjectInterface):
            self._version = interface.version
        elif isinstance(interface, ModuleObjectInterface):
            self._obj_type = interface.obj_type

        self._features = [GFeature(clu_client, object_id, fint) for fint in interface.features]
        self._methods = [GMethod(clu_client, object_id, mint) for mint in interface.methods]

    @property
    def clu_client(self) -> CluClient:
        return self._clu_client

    @property
    def name(self) -> str:
        return self._name

    @property
    def object_id(self) -> str:
        return self._object_id

    @property
    def version(self) -> int | None:
        return self._version

    @property
    def object_type(self) -> ModuleObjectType | None:
        return self._obj_type

    @property
    def features(self) -> list[GFeature]:
        return self._features

    @property
    def methods(self) -> list[GMethod]:
        return self._methods

    def get_feature_by_name(self, name: str) -> GFeature | None:
        for feature in self._features:
            if feature.name == name:
                return feature
            
        return None

    def get_feature_by_index(self, index: int) -> GFeature | None:
        for feature in self._features:
            if feature.index == index:
                return feature
            
        return None

    def get_method_by_name(self, name: str) -> GMethod | None:
        for method in self._methods:
            if method.name == name:
                return method
            
        return None

    def get_method_by_index(self, index: int) -> GMethod | None:
        for method in self._methods:
            if method.index == index:
                return method
            
        return None
    
    async def get_value_async(self, index: int):
        return await self._clu_client.get_value_async(self._object_id, index)

    def get_value(self, index: int):
        return asyncio.get_event_loop().run_until_complete(self.get_value_async(index))
    
    async def set_value_async(self, index: int, value) -> None: 
        await self._clu_client.set_value_async(self._object_id, index, value)

    def set_value(self, index: int, value) -> None:
        asyncio.get_event_loop().run_until_complete(self.set_value_async(index, value))
    
    async def execute_method_async(self, index: int, *args):
        return await self._clu_client.execute_method_async(self._object_id, index, args)

    def execute_method(self, index: int, *args):
        return asyncio.get_event_loop().run_until_complete(self.execute_method_async(index, args))