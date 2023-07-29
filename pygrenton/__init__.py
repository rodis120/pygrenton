
import asyncio
import os
import time

import tftpy

from .cipher import GrentonCypher
from .clu_client import CluClient
from .exceptions import ConfigurationDownloadError, ConfigurationParserError
from .gobject import GObject
from .interface_manager import InterfaceManager
from .parsers.config_json_parser import parse_json
from .parsers.config_parser import parse_clu_config
from .parsers.om_parser import parse_om


async def verify_async(ipaddress: str, key: str, iv: str) -> int | None:
    try:
        cipher = GrentonCypher(ipaddress, key, iv)
        clu_client = CluClient(ipaddress, 1234, cipher)
        
        return await clu_client.check_alive_async()
    except:
        return None

def verify(ipaddress: str, key: str, iv: str) -> int | None:
    return asyncio.get_event_loop().run_until_complete(ipaddress, key, iv)

class GrentonApi:
    
    objects: list[GObject]
    
    def __init__(self, ipaddress, key: str | bytes, iv: str | bytes, cache_dir = "pygrenton_cache", timeout: float = 1) -> None:
        self._ipaddress = ipaddress
        self._cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)
        
        self._cipher = GrentonCypher(key, iv)
        self._interface_manager = InterfaceManager(cache_dir)
        self._clu_client = CluClient(ipaddress, 1234, self._cipher, timeout)
        
        self._download_config()
        self._parse_config()
        
    async def check_alive_async(self) -> int:
        return await self._clu_client.check_alive_async()
    
    def check_alive(self) -> int:
        return self._clu_client.check_alive()
        
    def _download_config(self) -> None:
        try:
            tftp_client = tftpy.TftpClient(self._ipaddress, 69, options={"tsize": 0})
            self._clu_client.send_request("req_start_ftp")
            time.sleep(0.1)
            tftp_client.download("a:\\CONFIG.JSON", self._cache_dir + "/config.json")
            tftp_client.download("a:\\om.lua", self._cache_dir + "/om.lua")
            self._clu_client.send_request("req_tftp_stop")
        except:
            raise ConfigurationDownloadError
        
    def _parse_config(self) -> None:
        try:
            config_json = None
            om = None
            with open(self._cache_dir + "/config.json", "r") as f:
                config_json = parse_json(f)
            with open(self._cache_dir + "/om.lua", "r") as f:
                om = parse_om(f)
                
            self.objects = parse_clu_config(config_json, om, self._interface_manager, self._clu_client)
        except:
            raise ConfigurationParserError
            
        