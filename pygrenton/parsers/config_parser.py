
import logging

from ..clu_client import CluClient
from ..gclu import GCLU
from ..gmodule import GModule
from ..gobject import GObject
from ..interface_manager import InterfaceManager
from .config_json_parser import parse_json
from .om_parser import parse_om


def parse_clu_config(json_confg, om_config, interface_manager: InterfaceManager, clu_client: CluClient) -> GCLU:
    conf_json = parse_json(json_confg)
    om = parse_om(om_config)

    clu_interface = interface_manager.get_clu_interface(conf_json.hw_type, conf_json.fw_api_version)

    modules = []
    clu_objects = []
    gclu = GCLU(clu_client, om.names[om.this_clu.object_id], conf_json, clu_objects, modules)

    for sn, mod_objects in om.module_objects.items():
        mod_conf = conf_json.modules[sn]
        mod_int = interface_manager.get_module_interface(mod_conf.hw_type, mod_conf.fw_api_version)
        
        if mod_int is None:
            logging.warn("Missing module interface. hw_type: %d, fw_api_version: %d", mod_conf.hw_type, mod_conf.fw_api_version)
            continue
        
        gobjects = []
        for obj in mod_objects:
            obj_int = mod_int.objects[obj.object_type]
            obj_name = om.names[obj.object_id]
            
            gobj = GObject(gclu, obj_name, obj.object_id, obj_int)
            gobjects.append(gobj)
        
        gmodule = GModule(gclu, mod_int.name, mod_conf, gobjects)
        modules.append(gmodule)
        
    for clu_obj in om.clu_objects:
        obj_int = clu_interface.objects[clu_obj.object_type]
        obj_name = om.names[obj.object_id]
        
        gclu_obj = GObject(gclu, obj_name, clu_obj.object_id, obj_int)
        clu_objects.append(gclu_obj)

    return gclu
