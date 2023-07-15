
import logging

from ..clu_client import CluClient
from ..gobject import GObject
from ..interfaces import CluInterface, CluObjectInterface, ModuleObjectInterface
from ..interface_manager import InterfaceManager
from .config_json_parser import parse_json
from .om_parser import parse_om
from ..types import ModuleObjectType

def parse_clu_config(json_confg, om_config, interface_manager: InterfaceManager, clu_client: CluClient) -> list[GObject]:
    conf_json = parse_json(json_confg)
    om = parse_om(om_config)

    clu_interface = interface_manager.get_clu_interface(conf_json.hw_type, conf_json.fw_type, conf_json.fw_api_version)

    objects = []
    gclu = GObject(clu_client, om.getName(om.this_clu.object_id), om.this_clu.object_id, clu_interface)
    objects.append(gclu)

    for sn, mod_objects in om.module_objects.items():
        mod_conf = conf_json.modules[sn]
        mod_int = interface_manager.get_module_interface(mod_conf.hw_type, mod_conf.fw_type, mod_conf.fw_api_version)
        
        if mod_int is None:
            logging.warn("Missing module interface. hw_type: %d, fw_api_version: %d.", mod_conf.hw_type, mod_conf.fw_api_version)
            
            for obj in mod_objects:
                empty_interface = ModuleObjectInterface("unknown", obj.object_class, ModuleObjectType.NONE, [], [])
                gobj = GObject(clu_client, om.getName(obj.object_id) + "_UNKNOWN_INTERFACE", obj.object_id, empty_interface)
                objects.append(gobj) 
            continue
        
        for obj in mod_objects:
            obj_int = mod_int.objects[obj.object_class]
            obj_name = om.getName(obj.object_id)
            
            gobj = GObject(clu_client, obj_name, obj.object_id, obj_int)
            objects.append(gobj)
        
    for clu_obj in om.clu_objects:
        if clu_obj.object_class not in clu_interface.objects.keys():
            logging.warn("Missing clu objectc interface. object_type: %d.", clu_obj.object_class)
            # empty_interface = CluObjectInterface() # TODO: finish it later
            
            continue
        
        obj_int = clu_interface.objects[clu_obj.object_class]
        obj_name = om.getName(clu_obj.object_id)
        
        gclu_obj = GObject(clu_client, obj_name, clu_obj.object_id, obj_int)
        objects.append(gclu_obj)

    return objects
