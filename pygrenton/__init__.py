
import asyncio
import os
import threading
import time

import tftpy

from .cipher import GrentonCipher
from .clu_client import CluClient
from .exceptions import ConfigurationDownloadError, ConfigurationParserError
from .gobject import GObject
from .interface_manager import InterfaceManager
from .parsers.config_json_parser import parse_json
from .parsers.config_parser import parse_clu_config, CluConfig
from .parsers.om_parser import parse_om


def verify(ipaddress: str, key: str, iv: str) -> int | None:
    try:
        cipher = GrentonCipher(key, iv)
        clu_client = CluClient(ipaddress, 1234, cipher)
        
        return clu_client.check_alive()
    except:
        return None

async def verify_async(ipaddress: str, key: str, iv: str) -> int | None:
    return await asyncio.to_thread(verify, ipaddress, key, iv)

class GrentonApi:
    
    _clu_config: CluConfig
    
    _interface_manager: InterfaceManager = None
    _interface_manager_lock: threading.Lock = threading.Lock()
    
    def __init__(
        self,
        ipaddress,
        key: str | bytes,
        iv: str | bytes,
        cache_dir = "pygrenton_cache",
        timeout: float = 1,
        client_ip: str | None = None,
        client_port: int = 0,
        max_connections: int = 6
    ) -> None:
        self._ipaddress = ipaddress
        self._cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)
        
        self._cipher = GrentonCipher(key, iv)
        self._clu_client = CluClient(ipaddress, 1234, self._cipher, timeout, client_ip=client_ip, client_port=client_port, max_connections=max_connections)
        
        clu_sn = self._clu_client.check_alive()
        self._config_cache_dir = os.path.join(cache_dir, str(clu_sn))
        if not os.path.exists(self._config_cache_dir):
            os.mkdir(self._config_cache_dir)
        
        with self._interface_manager_lock:
            if self._interface_manager is None:
                GrentonApi._interface_manager = InterfaceManager(cache_dir)
        
        self._download_config()
        self._parse_config()
        
    @property
    def clu_config(self) -> CluConfig:
        return self._clu_config
        
    @property
    def objects(self) -> list[GObject]:
        return list(self._clu_config.objects_by_id.values())
    
    @property
    def objects_by_id(self) -> dict[str, GObject]:
        return self._clu_config.objects_by_id
    
    @property
    def objects_by_name(self) -> dict[str, GObject]:
        return self._clu_config.objects_by_name
        
    def get_objects_by_class(self, class_int: int) -> list[GObject]:
        return self._clu_config.objects_by_class.get(class_int, [])
    
    def get_object_by_id(self, object_id: str) -> GObject | None:
        return self._clu_config.objects_by_id.get(object_id, None)
    
    def get_object_by_name(self, name: str) -> GObject | None:
        return self._clu_config.objects_by_name.get(name, None)
        
    async def check_alive_async(self) -> int:
        return await self._clu_client.check_alive_async()
    
    def check_alive(self) -> int:
        return self._clu_client.check_alive()
        
    def register_update_handlers(self):
        self._clu_client.start_client_registration()
        
    def _download_config(self) -> None:
        
        # a trick to speed up the download by ignoring rest of the content of the file
        def skip_useless_part(data):
            msg =  data.data.decode()
            if msg.find("EventsFor") != -1:
                data.data = data.data[:-1]
        
        try:
            tftp_client = tftpy.TftpClient(self._ipaddress, 69, options={"tsize": 0})
            self._clu_client.send_request("req_start_ftp")
            time.sleep(0.01)
            tftp_client.download("a:\\CONFIG.JSON", os.path.join(self._config_cache_dir, "config.json"))
            tftp_client.download("a:\\om.lua", os.path.join(self._config_cache_dir, "om.lua"), packethook=skip_useless_part)
            self._clu_client.send_request("req_tftp_stop")
        except:
            raise ConfigurationDownloadError
        
    def _parse_config(self) -> None:
        try:
            config_json = None
            om = None
            with open(os.path.join(self._config_cache_dir, "config.json"), "r") as f:
                config_json = parse_json(f)
            with open(os.path.join(self._config_cache_dir, "om.lua"), "r") as f:
                om = parse_om(f)
                
            self._clu_config = parse_clu_config(config_json, om, self._interface_manager, self._clu_client)
        except:
            raise ConfigurationParserError
            
        