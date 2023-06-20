
import asyncio

from .gobject import GObject
from .interfaces import MethodInterface, ParameterInterface
from .types import CallType, DataType


class GMethod:
    _gobject: GObject
    _name: str
    _index: int
    _call_type: CallType

    _params: list[ParameterInterface]

    _return_type: DataType
    _unit: str | None
    
    def __init__(self, gobject: GObject, interface: MethodInterface) -> None:
        self._gobject = gobject
        self._name = interface.name
        self._index = interface.index
        self._call_type = interface.call
        self._params = interface.parameters
        self._return_type = interface.return_type
        self._unit = interface.unit

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
    def call_type(self) -> CallType:
        return self._call_type

    @property
    def parameters(self) -> list[ParameterInterface]:
        return self._params

    @property
    def return_type(self) -> DataType:
        return self._return_type

    @property
    def unit(self) -> str | None:
        return self._unit

    async def execute_method_async(self, *args):
        if len(args) != len(self._params):
            raise ValueError(f"Incorrect number of arguments: expected {len(self._params)}, provided {len(args)}")
        
        for arg, intr in zip(args, self._params):
            
            if intr.data_type == DataType.NUMBER:
                if not isinstance(arg, int) or not isinstance(arg, float):
                    raise ValueError(f"\"{type(arg)}\" is incorrect type for argument \"{intr.name}\". Expected a number")
            elif intr.data_type == DataType.STRING and not isinstance(arg, str):
                raise ValueError(f"\"{type(arg)}\" is incorrect type for argument \"{intr.name}\". Expected a string")

        if self._call_type == CallType.EXECUTE:
            return await self._gobject.execute_method_async(self._index, args)
        if self._call_type == CallType.GET:
            return await self._gobject.get_value_async(self._index)
        if self._call_type == CallType.SET:
            await self._gobject.set_value_async(self._index, args[0])

    def execute_method(self, *args):
        return asyncio.get_event_loop().run_until_complete(self.execute_method_async(args))
