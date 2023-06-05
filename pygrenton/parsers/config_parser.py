
from config_json_parser import parse_json
from om_parser import parse_om
from interface_manager import InterfaceManager
from gobjects import GCLU, GModule, GObject

def parse_clu_config(json_confg, om_config, interface_manager: InterfaceManager):
    clu = parse_json(json_confg)
    names, io_modules, objects = parse_om(om_config)
    
    gclu = GCLU() #TODO: do sth with it

    for serial_number, module_objects in io_modules.items():
        module = clu.modules[serial_number]
        module_interface = interface_manager.getModuleInterface(module.hw_type, module.fw_api_version)

        #TODO: create GModule
        gobjects = []

        for obj_id, obj_type, _ in module_objects:
            obj_interafce = module_interface.objects[obj_type]
            obj_name = names[obj_id]
            
            #TODO: create GObjects and add it into GModule
