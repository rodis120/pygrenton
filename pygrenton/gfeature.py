
import asyncio

from .clu_client import CluClient
from .exceptions import FeatureNotGettableError, FeatureNotSettableError
from .interfaces import FeatureInterface
from .types import DataType


class GFeature:
    _clu_client: CluClient
    _object_id: str
    _name: str
    _index: int
    _settable: bool
    _gettable: bool
    _data_type: DataType
    _unit: str

    _enum: dict | None
    _value_range: tuple[int, int] | None
    
    def __init__(self, clu_client: CluClient, object_id: str, interface: FeatureInterface) -> None:
        self._clu_client = clu_client
        self._object_id = object_id
        self._name = interface.name
        self._index = interface.index
        self._settable = interface.set
        self._gettable = interface.get
        self._data_type = interface.data_type
        self._unit = interface.unit
        self._enum = interface.enum
        self._value_range = interface.value_range

    @property
    def name(self) -> str:
        return self._name

    @property
    def parent(self) -> str:
        return self._object_id

    @property
    def index(self) -> int:
        return self._index

    @property
    def is_settable(self) -> bool:
        return self._settable

    @property
    def is_gettable(self) -> bool:
        return self._gettable

    @property
    def data_type(self) -> DataType:
        return self._data_type

    @property
    def unit(self) -> str:
        return self._unit

    @property
    def enum(self) -> dict | None:
        return self._enum

    @property
    def value_range(self) -> tuple[int, int] | None:
        return self._value_range

    async def get_value_async(self):
        if not self._gettable:
            raise FeatureNotGettableError(self._name)

        value = await self._clu_client.get_value_async(self._object_id, self._index)
        
        return self.data_type.convert_value(value)

    def get_value(self):
        return asyncio.get_event_loop().run_until_complete(self.get_value_async())

    async def get_value_mapped_async(self):
        val = await self.get_value_async()
        
        if self._enum is None or val not in self._enum.keys():
            return val
        
        return self._enum[val]
    
    def get_value_mapped(self):
        return asyncio.get_event_loop().run_until_complete(self.get_value_mapped_async())
    
    async def set_value_async(self, value):
        if not self._settable:
            raise FeatureNotSettableError(self._name)

        if self._enum is not None and value not in self._enum.keys():
            raise ValueError(f"Value: {value} is not in enum: {self._enum}")
        if self._value_range is not None and (value < self._value_range[0] or value > self._value_range[1]):
            raise ValueError(f"Value: {value} is not in value range: ({self._value_range[0]} - {self._value_range[1]})")
    
        await self._clu_client.set_value_async(self._object_id, self._index, value)

    def set_value(self, value) -> None:
        asyncio.get_event_loop().run_until_complete(self.set_value_async(value))
        
    def register_handler(self, handler) -> None:
        self._clu_client.register_value_change_handler(self._object_id, self._index, handler)

    def remove_handler(self) -> None:
        self._clu_client.remove_value_change_handler(self._object_id, self._index)
