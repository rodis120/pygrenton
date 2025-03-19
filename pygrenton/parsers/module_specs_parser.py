"""CLU module spcification parser."""

import json
from dataclasses import dataclass
from typing import Any, BinaryIO, TextIO


@dataclass
class ModuleSpecs:
    serial_number: int
    hw_type: int
    hw_version: int
    fw_type: int
    fw_api_version: int
    fw_version: int
    status: str

@dataclass
class CLUSpecs:
    serial_number: int
    mac: str
    hw_type: int
    hw_version: int
    fw_type: int
    fw_api_version: int
    fw_version: int
    status: str

    tfbus_modules: dict[int, ModuleSpecs]
    zwave_modules: dict[int, ModuleSpecs]

def _parse_module(json_elm: dict[str, Any]) -> ModuleSpecs:
    sn = json_elm["sn"]
    hw_type = json_elm["hwType"]
    hw_version = json_elm["hwVer"]
    fw_type = json_elm["fwType"]
    fw_api_version = json_elm["fwApiVer"]
    fw_version = json_elm["fwVer"]
    status = json_elm["status"]

    return ModuleSpecs(sn, hw_type, hw_version, fw_type, fw_api_version, fw_version, status)

def parse_specs_file(file: TextIO | BinaryIO) -> CLUSpecs:
    json_doc = json.load(file)

    serial_number = json_doc["sn"]
    mac = json_doc["mac"]
    hw_type = json_doc["hwType"]
    hw_version = json_doc["hwVer"]
    fw_type = json_doc["fwType"]
    fw_api_version = json_doc["fwApiVer"]
    fw_version = json_doc["fwVer"]
    status = json_doc["status"]

    tfbus_modules = {}
    zwave_modules = {}

    for elm in json_doc["tfbusDevices"]:
        mod = _parse_module(elm)
        tfbus_modules[mod.serial_number] = mod

    for elm in json_doc["zwaveDevices"]:
        mod = _parse_module(elm)
        zwave_modules[mod.serial_number] = mod

    return CLUSpecs(serial_number, mac, hw_type, hw_version, fw_type, fw_api_version, fw_version, status, tfbus_modules, zwave_modules)

