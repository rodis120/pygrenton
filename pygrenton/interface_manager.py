
import io
import logging
import pickle
import re
from pathlib import Path
from zipfile import ZipFile

import requests

from .interfaces import CluInterface, ModuleInterface
from .parsers.interfaces_parser import parse_interfaces

_LOGGER = logging.getLogger(__name__)

_OM_INTERFACES_ENDPOINT = "http://om.grenton.com/interfaces/v4/"
_OM_LATEST_INTERFACES = "device-interfaces.current"

def _get_latest_verion(timeout: float=1) -> str:
    resp = requests.get(_OM_INTERFACES_ENDPOINT + _OM_LATEST_INTERFACES, timeout=timeout)
    result = re.search(r"device.*zip", resp.text)

    if result is None:
        _LOGGER.error("Unable to get latest version of interface")
        return None

    return result.group(0)

def _get_current_version(cache_dir: Path) -> str | None:
    try:
        with Path.joinpath(cache_dir, "interfaces-version.txt").open() as version_file:
            return version_file.readline()
    except OSError:
        return None

def _download_interfaces(version: str, cache_dir: Path, timeout: float=1) -> None:
    resp = requests.get(_OM_INTERFACES_ENDPOINT + version, timeout=timeout)

    if len(resp.content) == 0:
        logging.error("Unable to download interfaces.")
        return

    try:
        with ZipFile(io.BytesIO(resp.content)) as zip_file:
            zip_file.extractall(cache_dir)

        with Path.joinpath(cache_dir, "interfaces-version.txt").open(mode="w") as version_file:
            version_file.write(version)
    except OSError:
        _LOGGER.exception("Unable to save interfaces.")

class InterfaceManager:
    #TODO: maybe create database for intefaces
    _clus: dict[int, list[CluInterface]] = None
    _modules: dict[int, list[ModuleInterface]] = None

    def __init__(self, cache_dir: Path|str) -> None:
        self._dir = Path(cache_dir)

        current_version = _get_current_version(cache_dir)
        newest_version = _get_latest_verion()

        if current_version != newest_version and newest_version is not None:
            _download_interfaces(newest_version, cache_dir)
            self._parse_interfaces()
            self._save_interface_cache()
        else:
            try:
                self._load_interface_cache()
            except:
                self._parse_interfaces()

    def get_clu_interface(self, hw_type: int, fw_type: int, api_version: int) -> CluInterface | None:
        clu_list = self._clus[hw_type]

        if clu_list is None:
            return None

        for clu in clu_list:
            if clu.fw_api_version == api_version and clu.fw_type == fw_type:
                return clu

        return clu_list[-1]

    def get_module_interface(self, hw_type: int, fw_type: int, api_version: int) -> ModuleInterface | None:
        mod_list = self._modules[hw_type]

        if mod_list is None:
            return None

        for mod in mod_list:
            if mod.fw_api_version == api_version and mod.fw_type == fw_type:
                return mod

        return mod_list[-1]

    def _parse_interfaces(self) -> None:
        clus, modules = parse_interfaces(self._dir + "/device-interfaces")
        self._clus = clus
        self._modules = modules
        self._save_interface_cache()

    def _save_list(self, list: list, filename: str) -> None:
        with Path.joinpath(self._dir, filename).open(mode="wb+") as file:
            pickle.dump(list, file)

    def _save_interface_cache(self) -> None:
        self._save_list(self._clus, "clus.cache")
        self._save_list(self._modules, "modules.cache")

    def _load_list(self, filename: str) -> list:
        with Path.joinpath(self._dir, filename).open(mode="rb") as file:
            return pickle.load(file)

    def _load_interface_cache(self) -> None:
        self._clus = self._load_list("clus.cache")
        self._modules = self._load_list("modules.cache")
