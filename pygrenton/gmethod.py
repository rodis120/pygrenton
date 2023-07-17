
import asyncio

from .clu_client import CluClient
from .interfaces import MethodInterface, ParameterInterface
from .types import CallType, DataType


class GMethod:
    _clu_client: CluClient
    _object_id: str
    _name: str
    _index: int
    _call_type: CallType

    _params: list[ParameterInterface]

    _return_type: DataType
    _unit: str | None
    
    def __init__(self, clu_client: CluClient, object_id: str, interface: MethodInterface) -> None:
        self._clu_client = clu_client
        self._object_id = object_id
        self._name = interface.name
        self._index = interface.index
        self._call_type = interface.call
        self._params = interface.parameters
        self._return_type = interface.return_type
        self._unit = interface.unit

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
                if not (isinstance(arg, int) or isinstance(arg, float)):
                    raise ValueError(f"\"{type(arg)}\" is incorrect type for argument \"{intr.name}\". Expected a number")
            elif intr.data_type == DataType.STRING and not isinstance(arg, str):
                raise ValueError(f"\"{type(arg)}\" is incorrect type for argument \"{intr.name}\". Expected a string")

        value = None
        if self._call_type == CallType.SET:
            return await self._clu_client.set_value_async(self._object_id, self._index, args[0])
        elif self._call_type == CallType.GET:
            value = await self._clu_client.get_value_async(self._object_id, self._index)
        else:
            value = await self._clu_client.execute_method_async(self._object_id, self._index, *args)
         
        return self.return_type.convert_value(value)

    def execute_method(self, *args):
        return asyncio.get_event_loop().run_until_complete(self.execute_method_async(*args))
