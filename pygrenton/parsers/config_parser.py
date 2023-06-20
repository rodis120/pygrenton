
from ..clu_client import CluClient
from ..gclu import GCLU
from ..gmodule import GModule
from ..gobject import GObject
from ..interface_manager import InterfaceManager
from .config_json_parser import parse_json
from .om_parser import parse_om


def parse_clu_config(json_confg, om_config, interface_manager: InterfaceManager, clu_client: CluClient) -> GCLU:
    clu = parse_json(json_confg)
    names, io_modules, objects = parse_om(om_config)

    clu_interface = interface_manager.get_clu_interface(clu.hw_type, clu.fw_api_version)

    modules = []
    clu_objects = []
    #TODO: fix it
    gclu = GCLU(clu_client, names[], clu, clu_objects, modules)

    for serial_number, module_objects in io_modules.items():
        module_config = clu.modules[serial_number]
        module_interface = interface_manager.get_module_interface(module_config.hw_type, module_config.fw_api_version)

        if module_interface is None:
            continue #TODO: fix it later

        gobjects = []
        for obj_id, obj_type, _ in module_objects:
            obj_interface = module_interface.objects[obj_type]
            obj_name = names[obj_id]

            obj = GObject(gclu, obj_name, obj_id, obj_interface)
            gobjects.append(obj)

        module = GModule(gclu, module_interface.name, module_config, gobjects)
        modules.append(module)

    #TODO: parse objects
    for obj_id, obj_class in objects:
        clu_interface.objects[obj_class] #ale tu jest burdel

    return gclu
