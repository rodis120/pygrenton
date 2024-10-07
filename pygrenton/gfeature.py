
import asyncio

from .clu_client import CluClient
from .exceptions import FeatureNotGettableError, FeatureNotSettableError
from .interfaces import FeatureInterface
from .types import DataType


class GFeature:
    
    def __init__(self, clu_client: CluClient, object_id: str, interface: FeatureInterface) -> None:
        self._clu_client = clu_client
        self._object_id = object_id
        self._interface = interface

    @property
    def name(self) -> str:
        return self._interface.name

    @property
    def parent(self) -> str:
        return self._object_id

    @property
    def index(self) -> int:
        return self._interface.index

    @property
    def is_settable(self) -> bool:
        return self._interface.set

    @property
    def is_gettable(self) -> bool:
        return self._interface.get

    @property
    def data_type(self) -> DataType:
        return self._interface.data_type

    @property
    def unit(self) -> str:
        return self._interface.unit

    @property
    def enum(self) -> dict | None:
        return self._interface.enum

    @property
    def value_range(self) -> tuple[int, int] | None:
        return self._interface.value_range

    async def get_value_async(self):
        if not self.is_gettable:
            raise FeatureNotGettableError(self.name)

        value = await self._clu_client.get_value_async(self._object_id, self.index)
        
        return self.data_type.convert_value(value)

    def get_value(self):
        return asyncio.get_event_loop().run_until_complete(self.get_value_async())

    async def get_value_mapped_async(self):
        val = await self.get_value_async()
        
        if self.enum is None or val not in self.enum.keys():
            return val
        
        return self.enum[val]
    
    def get_value_mapped(self):
        return asyncio.get_event_loop().run_until_complete(self.get_value_mapped_async())
    
    async def set_value_async(self, value):
        if not self.is_settable:
            raise FeatureNotSettableError(self.name)

        if self.enum is not None and value not in self.enum.keys():
            raise ValueError(f"Value: {value} is not in enum: {self.enum}")
        if self.value_range is not None and (value < self.value_range[0] or value > self.value_range[1]):
            raise ValueError(f"Value: {value} is not in value range: ({self.value_range[0]} - {self.value_range[1]})")
    
        await self._clu_client.set_value_async(self._object_id, self.index, value)

    def set_value(self, value) -> None:
        asyncio.get_event_loop().run_until_complete(self.set_value_async(value))
        
    def register_handler(self, handler) -> None:
        self._clu_client.register_value_change_handler(self._object_id, self.index, handler)

    def remove_handler(self) -> None:
        self._clu_client.remove_value_change_handler(self._object_id, self.index)
