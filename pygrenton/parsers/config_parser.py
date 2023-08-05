
import logging

from ..clu_client import CluClient
from ..config_objects import CLUConfig
from ..gobject import GObject
from ..interface_manager import InterfaceManager
from ..interfaces import CluObjectInterface, ModuleObjectInterface
from ..types import ModuleObjectType
from .om_parser import OMEndpoints


def parse_clu_config(conf_json: CLUConfig, om: OMEndpoints, interface_manager: InterfaceManager, clu_client: CluClient) -> tuple[dict[int, list[GObject]], dict[str, GObject], dict[str, GObject]]:
    clu_interface = interface_manager.get_clu_interface(conf_json.hw_type, conf_json.fw_type, conf_json.fw_api_version)

    objects_by_class: dict[int, list[GObject]] = {}
    objects_by_id: dict[str, GObject] = {}
    objects_by_name: dict[str, GObject] = {}
    
    def add_object(obj: GObject) -> None:
        if obj.object_class in objects_by_class.keys():
            objects_by_class[obj.object_class].append(obj)
        else:
            objects_by_class[obj.object_class] = [obj]
        
        objects_by_id[obj.object_id] = obj
        objects_by_name[obj.name] = obj
    
    gclu = GObject(clu_client, om.getName(om.this_clu.object_id), om.this_clu.object_id, clu_interface)
    add_object(gclu)

    for sn, mod_objects in om.module_objects.items():
        mod_conf = conf_json.modules[sn]
        mod_int = interface_manager.get_module_interface(mod_conf.hw_type, mod_conf.fw_type, mod_conf.fw_api_version)
        
        if mod_int is None:
            logging.warn("Missing module interface. hw_type: %d, fw_api_version: %d.", mod_conf.hw_type, mod_conf.fw_api_version)
            
            for obj in mod_objects:
                empty_interface = ModuleObjectInterface("unknown", obj.object_class, ModuleObjectType.NONE, [], [])
                gobj = GObject(clu_client, om.getName(obj.object_id), obj.object_id, empty_interface)
                add_object(gobj) 
            continue
        
        for obj in mod_objects:
            obj_int = mod_int.objects[obj.object_class]
            obj_name = om.getName(obj.object_id)
            
            gobj = GObject(clu_client, obj_name, obj.object_id, obj_int)
            add_object(gobj)
        
    for clu_obj in om.clu_objects:
        if clu_obj.object_class not in clu_interface.objects.keys():
            logging.warn("Missing clu objectc interface. object_type: %d.", clu_obj.object_class)
            
            empty_interface = CluObjectInterface("unknown", clu_obj.object_class, 0)
            gobj = GObject(clu_client, om.getName(clu_obj.object_id), clu_obj.object_id, empty_interface)
            add_object(gobj)
            continue
        
        obj_int = clu_interface.objects[clu_obj.object_class]
        obj_name = om.getName(clu_obj.object_id)
        
        gclu_obj = GObject(clu_client, obj_name, clu_obj.object_id, obj_int)
        add_object(gclu_obj)

    return objects_by_class, objects_by_id, objects_by_name
