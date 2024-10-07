
import asyncio
from typing import Any

from .clu_client import CluClient
from .interfaces import MethodInterface, ParameterInterface
from .types import CallType, DataType


class GMethod:

    def __init__(self, clu_client: CluClient, object_id: str, interface: MethodInterface) -> None:
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
    def call_type(self) -> CallType:
        return self._interface.call

    @property
    def parameters(self) -> list[ParameterInterface]:
        return self._interface.parameters

    @property
    def return_type(self) -> DataType:
        return self._interface.return_type

    @property
    def unit(self) -> str | None:
        return self._interface.unit

    async def execute_method_async(self, *args: Any):
        if len(args) != len(self.parameters):
            msg = f"Incorrect number of arguments: expected {len(self.parameters)}, provided {len(args)}"
            raise ValueError(msg)

        for arg, intr in zip(args, self.parameters, strict=False):
            if intr.data_type == DataType.NUMBER:
                if not (isinstance(arg, int) or isinstance(arg, float)):
                    raise ValueError(f"\"{type(arg)}\" is incorrect type for argument \"{intr.name}\". Expected a number")
            elif intr.data_type == DataType.STRING and not isinstance(arg, str):
                raise ValueError(f"\"{type(arg)}\" is incorrect type for argument \"{intr.name}\". Expected a string")

        value = None
        if self.call_type == CallType.SET:
            return await self._clu_client.set_value_async(self._object_id, self.parameters, args[0])
        if self.call_type == CallType.GET:
            value = await self._clu_client.get_value_async(self._object_id, self.parameters)
        else:
            value = await self._clu_client.execute_method_async(self._object_id, self.index, *args)

        return self.return_type.convert_value(value)

    def execute_method(self, *args: Any):
        return asyncio.get_event_loop().run_until_complete(self.execute_method_async(*args))
