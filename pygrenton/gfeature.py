
import asyncio

from .exceptions import FeatureNotGettableError, FeatureNotSettableError
from .gobject import GObject
from .interfaces import FeatureInterface
from .types import DataType


class GFeature:
    _gobject: GObject
    _name: str
    _index: int
    _settable: bool
    _gettable: bool
    _data_type: DataType
    _unit: str

    _enum: list | None
    _value_range: tuple[int, int] | None
    
    def __init__(self, gobject, interface: FeatureInterface) -> None:
        self._gobject = gobject
        self._name = interface.name
        self._index = interface.index
        self._settable = interface.set
        self._gettable = interface.get
        self._data_type = interface.data_type
        self._unit = interface.unit
        self._enum = interface.enum
        self._value_range = interface.value_range

    @property
    def parent(self) -> GObject:
        return self._gobject

    @property
    def name(self) -> str:
        return self._name

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
    def enum(self) -> list | None:
        return self._enum

    @property
    def value_range(self) -> tuple[int, int] | None:
        return self._value_range

    async def get_value_async(self):
        if not self._gettable:
            raise FeatureNotGettableError(self._name)

        return await self._gobject.get_value_async(self._index)

    def get_value(self):
        return asyncio.get_event_loop().run_until_complete(self.get_value_async())

    async def set_value_async(self, value):
        if not self._settable:
            raise FeatureNotSettableError(self._name)

        if self._enum is not None and value not in self._enum:
            raise ValueError(f"Value: {value} is not in enum: {self._enum}")
        if self._value_range is not None and (value < self._value_range[0] or value > self._value_range[1]):
            raise ValueError(f"Value: {value} is not in value range: ({self._value_range[0]} - {self._value_range[1]})")
    
        await self._gobject.set_value_async(self._index, value)

    def set_value(self, value) -> None:
        asyncio.get_event_loop().run_until_complete(self.set_value_async(value))
