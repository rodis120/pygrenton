
import json
from config_objects import CLUConfig, ModuleConfig

def _parse_module(json_elm) -> ModuleConfig:
    sn = json_elm["sn"]
    hw_type = json_elm["hwType"]
    hw_version = json_elm["hwVer"]
    fw_type = json_elm["fwType"]
    fw_api_version = json_elm["fwApiVer"]
    fw_version = json_elm["fwVer"]
    status = json_elm["status"]

    return ModuleConfig(sn, hw_type, hw_version, fw_type, fw_api_version, fw_version, status)

def parse_json(file) -> CLUConfig:
    json_doc = json.load(file)
    
    serial_number = json_doc["sn"]
    mac = json_doc["mac"]
    hw_type = json_doc["hwType"]
    hw_version = json_doc["hwVer"]
    fw_type = json_doc["fwType"]
    fw_api_version = json_doc["fwApiVer"]
    fw_version = json_doc["fwVer"]
    status = json_doc["status"]

    modules = {}

    for elm in json_doc["tfbusDevices"]:
        mod = _parse_module(elm)
        modules[mod.serial_number] = mod

    for elm in json_doc["zwaveDevices"]:
        mod = _parse_module(elm)
        modules[mod.serial_number] = mod

    return CLUConfig(serial_number, mac, hw_type, hw_version, fw_type, fw_api_version, fw_version, status, modules)

