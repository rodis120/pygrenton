
import json
from modules import Module, CLU_Module

def _parse_module(json_elm) -> Module:
    sn = json_elm["sn"]
    hw_type = json_elm["hwType"]
    hw_version = json_elm["hwVer"]
    fw_type = json_elm["fwType"]
    fw_api_version = json_elm["fwApiVer"]
    fw_version = json_elm["fwVer"]
    status = json_elm["status"]

    return Module(sn, hw_type, hw_version, fw_type, fw_api_version, fw_version, status)

def parse_json(file) -> CLU_Module:
    json_doc = json.load(file)
    
    serial_number = json_doc["sn"]
    mac = json_doc["mac"]
    hw_type = json_doc["hwType"]
    hw_version = json_doc["hwVer"]
    fw_type = json_doc["fwType"]
    fw_api_version = json_doc["fwApiVer"]
    fw_version = json_doc["fwVer"]
    status = json_doc["status"]

    modules = [_parse_module(jelm) for jelm in json_doc["tfbusDevices"]]

    return CLU_Module(serial_number, mac, hw_type, hw_version, fw_type, fw_api_version, fw_version, status, modules)

