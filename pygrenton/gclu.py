
import asyncio

from .clu_client import CluClient
from .gmodule import GModule, IModule, IHasGObjects
from .gobject import GObject
from .config_objects import CLUConfig


class GCLU(IModule, IHasGObjects):

    _clu_client: CluClient
    _clu_gobject: GObject

    _modules: list[GModule]

    #TODO: choose between creating IHasModules class or implementing it inside GCLU class
    def __init__(self, clu_client: CluClient, name: str, config: CLUConfig, gobjects: list[GObject], gmodules: list[GModule]) -> None:
        self._clu_client = clu_client
        self._modules = gmodules
        IModule.__init__(self, name, config)
        IHasGObjects.__init__(self, gobjects)

    @property
    def clu_client(self) -> CluClient:
        return self._clu_client

    @property
    def clu_gobject(self) -> GObject:
        return self._clu_gobject

    @property
    def modules(self) -> list[GModule]:
        return self._modules

    def get_modules_by_type(self, hw_type: int) -> list[GModule]:
        return [mod for mod in self._modules if mod.hw_type == hw_type]

    def get_modules_by_name(self, name: str) -> list[GModule]:
        return [mod for mod in self._modules if mod.name == name]

    def get_module_by_sn(self, serial_number: int) -> GModule | None:
        for mod in self._modules:
            if mod.serial_number == serial_number:
                return mod

        return None

    async def send_command_async(self, cmd: str) -> str:
        if not isinstance(cmd, str):
            raise ValueError("Argument is expected to be a string.")

        return await self.clu_client.send_request_async(cmd)

    def send_command(self, cmd: str) -> str:
        return asyncio.get_event_loop().run_until_complete(self.send_command_async(cmd))