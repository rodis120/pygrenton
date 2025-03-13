
import asyncio
from typing import Any
from xml.etree.ElementTree import Element

from .clu_client import CluClient
from .types import CallType


class GMethod:

    def __init__(self, clu_client: CluClient, object_id: str, interface: Element) -> None:
        self._clu_client = clu_client
        self._object_id = object_id
        self._interface = interface

    @property
    def name(self) -> str:
        return self._interface.attrib.get("name", "")

    @property
    def parent(self) -> str:
        return self._object_id

    @property
    def index(self) -> int:
        return int(self._interface.attrib["index"])

    @property
    def call_type(self) -> CallType:
        return CallType(self._interface.attrib.get("call"))

    # TODO: Fix it later
    # @property
    # def parameters(self) -> list[ParameterInterface]:
    #     return self._interface.parameters

    @property
    def return_type(self) -> str | None:
        return self._interface.attrib.get("return")

    @property
    def unit(self) -> str | None:
        return self._interface.attrib.get("unit")

    @property
    def interface(self) -> Element:
        return self._interface

    def execute_method(self, *args: Any) -> Any | None:
        if self.call_type == CallType.SET:
            return self._clu_client.set_value(self._object_id, self.index, args[0])
        if self.call_type == CallType.GET:
            return self._clu_client.get_value(self._object_id, self.index)

        return self._clu_client.execute_method(self._object_id, self.index, *args)

    async def execute_method_async(self, *args: Any) -> Any | None:
        return await asyncio.to_thread(self.execute_method, *args)
