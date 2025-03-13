"""Object interface parser."""

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

_TAGS_TO_PRUNE = [
    "events",
    "hint",
    "desc",
    "modulesVersionConstraints",
    "options",
]

@dataclass(eq=True, frozen=True)
class CluIndex:
    hw_type: int
    fw_type: int
    api_version: int

@dataclass(eq=True, frozen=True)
class ModuleIndex:
    hw_type: int
    fw_type: int
    api_version: int

@dataclass(eq=True, frozen=True)
class VirtualObjectIndex:
    name: str
    version: int

def _create_clu_index(interface_root: ET.Element) -> CluIndex:
    root = interface_root
    hw_type = int(root.attrib.get("hardwareType"), base=16)
    fw_type = int(root.attrib.get("firmwareType"), base=16)
    api_version = int(root.attrib.get("firmwareVersion"), base=16)
    return CluIndex(hw_type, fw_type, api_version)

def _create_module_index(interface_root: ET.Element) -> ModuleIndex:
    module = interface_root
    firmware = module[0]
    hw_type = int(module.attrib.get("typeId"), base=16)
    fw_type = int(firmware.attrib.get("typeId"), base=16)
    api_version = int(firmware.attrib.get("version"), base=16)
    return ModuleIndex(hw_type, fw_type, api_version)

def _create_virtual_object_index(interface_root: ET.Element) -> VirtualObjectIndex:
    root = interface_root
    name = root.attrib.get("name")
    version = int(root.attrib.get("version"), base=16)
    return VirtualObjectIndex(name, version)

def _prune_interface_tree(tree: ET.ElementTree) -> None:
    root = tree.getroot()

    for tag in _TAGS_TO_PRUNE:
        for elem in root.findall(tag):
            root.remove(elem)

def parse_interface_file(path: Path) -> ET.ElementTree:
    tree = ET.parse(path)
    _prune_interface_tree(tree)
    return tree

def parse_interfaces(path: Path):

    clus: dict[CluIndex, ET.Element] = {}
    modules: dict[ModuleIndex, ET.Element] = {}
    virtual_objects: dict[VirtualObjectIndex, ET.Element] = {}

    if not path.is_dir():
        msg = f"Invalid path: {path}"
        raise ValueError(msg)

    for file_path in path.iterdir():
        interface_tree = parse_interface_file(file_path)

        root = interface_tree.getroot()
        match root.tag:
            case "clu":
                index = _create_clu_index(root)
                clus[index] = root
            case "module":
                index = _create_module_index(root)
                modules[index] = root
            case "object":
                index = _create_virtual_object_index(root)
                virtual_objects[index] = root
            case _:
                _LOGGER.debug("Unknown interface type: %s", root.tag)

    for clu in clus.values():
        objects = clu.find("objects")
        interfaces = []
        for obj in objects:
            index = _create_virtual_object_index(obj)
            interfaces.append(virtual_objects[index])

        objects.clear()
        for interface in interfaces:
            objects.append(interface)

    return clus, modules
