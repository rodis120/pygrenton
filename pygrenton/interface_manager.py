
from parsers.interfaces_parser import parse_interfaces
from interfaces import CluObjectInterface, CluInterface, ModuleInterface

class InterfaceManager:
    #TODO: implement dynamic interface downloading
    #TODO: implement interface cashing
    #TODO: maybe create database for intefaces

    def __init__(self, interfaces_dir) -> None:
        self._dir = interfaces_dir

        clus, modules, objects = parse_interfaces(interfaces_dir)
        self._clus = clus
        self._modules = modules
        self._objects = objects

    def get_clu_interface(self, hw_type, version) -> CluInterface | None:
        clu_lst = self._clus[hw_type]

        if clu_lst is None:
            return None
        
        for clu in clu_lst:
            if clu.fw_api_version == version:
                return clu
            
        return clu_lst[-1]

    def get_module_interface(self, hw_type, version) -> ModuleInterface | None:
        mod_lst = self._modules[hw_type]

        if mod_lst is None:
            return None
        
        for mod in mod_lst:
            if mod.fw_api_version == version:
                return mod
            
        return mod_lst[-1]

    def get_clu_object_interface(self, obj_type, version) -> CluObjectInterface | None:
        obj_lst = self._objects[obj_type]

        if obj_lst is None:
            return None
        
        for obj in obj_lst:
            if obj.version == version:
                return obj
            
        return obj_lst[-1]

