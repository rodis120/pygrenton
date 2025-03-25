
import logging
from dataclasses import dataclass
from xml.etree.ElementTree import Element

from ..clu_client import CluClient
from ..gobject import GObject
from ..interface_manager import InterfaceManager
from .module_specs_parser import CLUSpecs
from .om_parser import OMEndpoints

_LOGGER = logging.getLogger(__name__)

@dataclass
class CluConfig:
    om_config: OMEndpoints
    conf_json: CLUSpecs
    gobjects: dict[str, GObject]

def _dummy_clu_interface(hw_type: int, fw_type: int, api_version: int) -> Element:
    return Element(
        tag="CLU",
        attrib={
            "typeName": "UNKNOWN_CLU",
            "hardwareType": hex(hw_type)[2:],
            "firmwareType": hex(fw_type)[2:],
            "firmwareVersion": hex(api_version)[2:]
        }
    )

def _dummy_module_interface(hw_type: int, fw_type: int, api_version: int) -> Element:
    module = Element(tag="module", attrib={"typeId": hex(hw_type)[2:], "name": "UNKNOWN_MODULE"})
    firmware = Element(tag="firmware", attrib={"typeId": hex(fw_type)[2:], "version": hex(api_version)[2:]})
    module.append(firmware)
    return module

def _dummy_object_interface(obj_class: int, name: str="UNKNOWN_OBJECT") -> Element:
    return Element(tag="object", attrib={"class": obj_class, "name": name})

def parse_clu_config(specs: CLUSpecs, om: OMEndpoints, interface_manager: InterfaceManager, clu_client: CluClient) -> CluConfig:
    objects_by_id: dict[str, GObject] = {}

    def add_object(obj: GObject) -> None:
        objects_by_id[obj.object_id] = obj

    clu_interface = interface_manager.get_clu_interface(specs.hw_type, specs.fw_type, specs.fw_api_version)
    if clu_interface in None:
        _LOGGER.debug("Missing object interface. hw_type: %d, fw_type: %d, fw_api_version: %d.", specs.hw_type, specs.fw_type, specs.fw_api_version)
        clu_interface = _dummy_clu_interface(specs.hw_type, specs.fw_type, specs.fw_api_version)
    gclu = GObject(clu_client, om.get_name(om.local_clu.object_id), om.local_clu.object_id, clu_interface, clu_interface)
    add_object(gclu)

    for sn, mod_objects in om.module_objects.items():
        mod_specs = specs.tfbus_modules[sn] #TODO: do something with z-wave modules, idk how clu represents them in om
        mod_int = interface_manager.get_module_interface(mod_specs.hw_type, mod_specs.fw_type, mod_specs.fw_api_version)

        if mod_int is None:
            _LOGGER.debug("Missing module interface. hw_type: %d, fw_api_version: %d.", mod_specs.hw_type, mod_specs.fw_api_version)

            module_interface = _dummy_module_interface(mod_specs.hw_type, mod_specs.fw_type, mod_specs.fw_api_version)
            for obj in mod_objects:
                dummy_interface = _dummy_object_interface(obj.object_class)
                gobj = GObject(clu_client, om.get_name(obj.object_id), obj.object_id, dummy_interface, module_interface)
                add_object(gobj)
            continue

        for obj in mod_objects:
            obj_int = mod_int.find(f"object[@class='{obj.object_class}']")

            if obj_int is None:
                _LOGGER.debug("Missing object interface. class: %d, hw_type: %d, fw_api_version: %d.", obj.object_class, mod_specs.hw_type, mod_specs.fw_api_version)
                continue

            obj_name = om.get_name(obj.object_id)

            gobj = GObject(clu_client, obj_name, obj.object_id, obj_int)
            add_object(gobj)

    object_interfaces = {int(obj.attrib["class"]): obj for obj in clu_interface.iter("object")}
    for clu_obj in om.clu_objects:
        if clu_obj.object_class not in object_interfaces:
            _LOGGER.debug("Missing clu objectc interface. object_type: %d.", clu_obj.object_class)

            dummy_interface = _dummy_object_interface(clu_obj.object_class)
            gobj = GObject(clu_client, om.get_name(clu_obj.object_id), clu_obj.object_id, dummy_interface, clu_interface)
            add_object(gobj)
            continue

        obj_int = object_interfaces[clu_obj.object_class]
        obj_name = om.get_name(clu_obj.object_id)

        gclu_obj = GObject(clu_client, obj_name, clu_obj.object_id, obj_int, clu_interface)
        add_object(gclu_obj)

    return CluConfig(om, specs, objects_by_id)
