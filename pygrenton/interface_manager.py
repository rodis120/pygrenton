
import io
import logging
import pickle
import re
from zipfile import ZipFile

import requests

from .interfaces import CluInterface, ModuleInterface
from .parsers.interfaces_parser import parse_interfaces

_OM_INTERFACES_ENDPOINT = "http://om.grenton.com/interfaces/v4/"
_OM_NEWEST_INTERFACES = "device-interfaces.current"

def _get_newest_verion() -> str:
    resp = requests.get(_OM_INTERFACES_ENDPOINT + _OM_NEWEST_INTERFACES)
    result = re.search(r"device.*zip", resp.text)
    if result is None:
        logging.error("Unable to get latest version of interface")
        return None
    return result.group(0)

def _get_current_version(dir) -> str | None:
    try:
        version_file = open(dir + "/interfaces-version.txt", "r")
        return version_file.readline()
    except IOError:
        return None
    
def _download_interfaces(version, directory) -> None:
    resp = requests.get(_OM_INTERFACES_ENDPOINT + version)
    
    if len(resp.content) == 0:
        logging.error("Unable to download interfaces.")
        return
    
    try:
        with ZipFile(io.BytesIO(resp.content)) as zip:
            zip.extractall(directory)
            
        with open(directory + "/interfaces-version.txt", "w") as version_file:
            version_file.write(version)
    except IOError as e:
        logging.error("Unable to save interfaces. Error message: %s", e.strerror)
    
class InterfaceManager:
    #TODO: maybe create database for intefaces
    _clus: list[CluInterface] = None
    _modules: list[ModuleInterface] = None

    def __init__(self, cache_dir: str) -> None:
        self._dir = cache_dir

        current_version = _get_current_version(cache_dir)
        newest_version = _get_newest_verion()
        
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
    
    def _save_list(self, list, filename) -> None:
        with open(self._dir + '/' + filename, 'wb') as file:
            pickle.dump(list, file)
    
    def _save_interface_cache(self) -> None:
        self._save_list(self._clus, "clus.cache")
        self._save_list(self._modules, "modules.cache")
        
    def _load_list(self, filename) -> list:
        with open(self._dir + "/" + filename, "rb") as file:
            return pickle.load(file)
        
    def _load_interface_cache(self) -> None:
        self._clus = self._load_list("clus.cache")
        self._modules = self._load_list("modules.cache")
    