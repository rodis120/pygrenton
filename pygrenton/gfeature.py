
import asyncio
from typing import Any

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

    def get_value(self) -> Any:
        if not self.is_gettable:
            raise FeatureNotGettableError(self.name)

        value = self._clu_client.get_value(self._object_id, self.index)

        return self.data_type.convert_value(value)

    async def get_value_async(self) -> Any:
        return await asyncio.to_thread(self.get_value_async)

    def get_value_mapped(self) -> Any:
        val = self.get_value_async()

        if self.enum is None or val not in self.enum.keys():
            return val

        return self.enum[val]

    async def get_value_mapped_async(self) -> Any:
        return await asyncio.to_thread(self.get_value_mapped)

    def set_value(self, value: Any) -> None:
        if not self.is_settable:
            raise FeatureNotSettableError(self.name)

        if self.enum is not None and value not in self.enum.keys():
            raise ValueError(f"Value: {value} is not in enum: {self.enum}")
        if self.value_range is not None and (value < self.value_range[0] or value > self.value_range[1]):
            raise ValueError(f"Value: {value} is not in value range: ({self.value_range[0]} - {self.value_range[1]})")

        self._clu_client.set_value(self._object_id, self.index, value)

    async def set_value_async(self, value: Any) -> None:
        await asyncio.to_thread(self.set_value, value)

    def register_handler(self, handler: Any) -> None:
        self._clu_client.register_value_change_handler(self._object_id, self.index, handler)

    def remove_handler(self, handler: Any) -> None:
        self._clu_client.remove_value_change_handler(self._object_id, self.index, handler)
