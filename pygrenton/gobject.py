
from typing import Any
from xml.etree.ElementTree import Element

from .clu_client import CluClient
from .gfeature import GFeature
from .gmethod import GMethod


class GObject:

    def __init__(self, clu_client: CluClient, name: str, object_id: str, interface: Element) -> None:
        self._clu_client = clu_client
        self._name = name
        self._object_id = object_id
        self._interface = interface

        if interface.tag == "clu":
            self._obj_class = 0
        else:
            self._obj_class = int(interface.attrib["class"])

        self._features = [GFeature(clu_client, object_id, fint) for fint in interface.findall("feature")]
        self._methods = [GMethod(clu_client, object_id, mint) for mint in interface.findall("method")]

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
    def object_class(self) -> int:
        return self._obj_class

    @property
    def object_class_name(self) -> str:
        return self._interface.attrib.get("name", "")

    @property
    def features(self) -> list[GFeature]:
        return self._features

    @property
    def methods(self) -> list[GMethod]:
        return self._methods

    @property
    def interface(self) -> Element:
        return self._interface

    def has_feature(self, key: int | str) -> bool:
        if isinstance(key, int):
            return self.get_feature_by_index(key) is not None
        if isinstance(key, str):
            return self.get_feature_by_name(key) is not None

        raise TypeError("Key must either be an int or a string.")

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

    def has_method(self, key: int | str) -> bool:
        if isinstance(key, int):
            return self.get_method_by_index(key) is not None
        if isinstance(key, str):
            return self.get_method_by_name(key) is not None

        raise TypeError("Key must either be an int or a string.")

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

    async def get_value_async(self, index: int) -> Any | None:
        return await self._clu_client.get_value_async(self._object_id, index)

    def get_value(self, index: int) -> Any | None:
        return self._clu_client.get_value(self._object_id, index)

    async def set_value_async(self, index: int, value: Any) -> None:
        await self._clu_client.set_value_async(self._object_id, index, value)

    def set_value(self, index: int, value: Any) -> None:
        self._clu_client.set_value(self._object_id, index, value)

    async def execute_method_async(self, index: int, *args: Any) -> Any | None:
        return await self._clu_client.execute_method_async(self._object_id, index, args)

    def execute_method(self, index: int, *args: Any) -> Any | None:
        return self._clu_client.execute_method(self._object_id, index, args)
