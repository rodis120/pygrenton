
import os
import xml.dom.minidom as md
from xml.dom.minidom import Element
from ..interfaces import *

def _parse_feature(elm: Element) -> FeatureInterface:
    name = elm.getAttribute("name")
    index = int(elm.getAttribute("index"))
    get = elm.getAttribute("get") == "true"
    set = elm.getAttribute("set") == "true"
    data_type = DataType(elm.getAttribute("type"))
    unit = elm.getAttribute("unit")

    value_range = None
    if elm.hasAttribute("range"):
        value_range = (int(i) for i in elm.getAttribute("range").split("-"))

    enum = None
    if elm.hasAttribute("enum"):
        if data_type == DataType.STRING:
            enum = [s for s in elm.getAttribute("enum").split(",")]
        elif data_type == DataType.NUMBER:
            enum = [int(s) for s in elm.getAttribute("enum").split(",")]

    return FeatureInterface(name, index, get, set, data_type, unit, enum, value_range)

def _parse_parameter(elm: Element) -> ParameterInterface:
    name = elm.getAttribute("name")
    data_type = DataType(elm.getAttribute("type"))
    unit = elm.getAttribute("unit")

    value_range = None
    if elm.hasAttribute("range"):
        value_range = (int(x) for x in elm.getAttribute("range").split("-"))

    enum = None
    if elm.hasAttribute("enum"):
        if data_type == DataType.STRING:
            enum = [s for s in elm.getAttribute("enum").split(",")]
        elif data_type == DataType.NUMBER:
            enum = [int(s) for s in elm.getAttribute("enum").split(",")]

    return ParameterInterface(name, data_type, unit, enum, value_range)

def _parse_method(elm: Element) -> MethodInterface:
    call = CallType(elm.getAttribute("call"))
    index = int(elm.getAttribute("index"))
    name = elm.getAttribute("name")

    return_value = DataType(elm.getAttribute("return"))

    params = [_parse_parameter(par) for par in elm.getElementsByTagName("param")]

    return MethodInterface(name, index, call, params, return_value, None)

def _parse_module_object(xml: Element) -> ModuleObjectInterface:

    obj_class = int(xml.getAttribute("class"))
    name = xml.getAttribute("name")
    type = ModuleObjectType(xml.getAttribute("type"))

    features = [_parse_feature(x) for x in xml.getElementsByTagName("feature")]
    methods = [_parse_method(x) for x in xml.getElementsByTagName("methods")]

    return ModuleObjectInterface(name, obj_class, type, features, methods)

def parse_clu_object_xml(file) -> CluObjectInterface:
    dom = md.parse(file)

    obj = dom.getElementsByTagName("object")[0]
    obj_class = int(obj.getAttribute("class"))
    name = obj.getAttribute("name")
    version = int(obj.getAttribute("version"))

    features = [_parse_feature(xml) for xml in dom.getElementsByTagName("feature")]
    methods = [_parse_method(xml) for xml in dom.getElementsByTagName("methods")]

    return CluObjectInterface(name, obj_class, version, features, methods)

def parse_module_xml(file) -> ModuleInterface:
    dom = md.parse(file)

    mod = dom.getElementsByTagName("module")[0]
    name = mod.getAttribute("name")
    hw_type = int(mod.getAttribute("typeId"), 16)

    fw = dom.getElementsByTagName("firmware")[0]
    fw_type = int(fw.getAttribute("typeId"), 16)
    fw_api_version = int(fw.getAttribute("version"), 16)

    objects = [_parse_module_object(obj) for obj in dom.getElementsByTagName("object")]

    return ModuleInterface(name, hw_type, fw_type, fw_api_version, objects)

def parse_clu_xml(file) -> CluInterface:
    dom = md.parse(file)

    clu = dom.getElementsByTagName("CLU")[0]
    name = clu.getAttribute("typeName")
    hw_type = int(clu.getAttribute("hardwareType"), 16)
    hw_version = int(clu.getAttribute("hardwareVersion"), 16)
    fw_type = int(clu.getAttribute("firmwareType"), 16)
    fw_version = int(clu.getAttribute("firmwareVersion"), 16)

    features = [_parse_feature(x) for x in dom.getElementsByTagName("feature")]
    methods = [_parse_method(x) for x in dom.getElementsByTagName("methods")]

    objects = {}
    for obj in dom.getElementsByTagName("object"):
        obj_name = obj.getAttribute("name")
        obj_version = int(obj.getAttribute("version"))
        objects[obj_name] = obj_version

    return CluInterface(name, hw_type, hw_version, fw_type, fw_version, features, methods, objects)

def _append_elm(dict, key, val):
    if key in dict:
        dict[key] += val
    else:
        dict[key] = [val]

def parse_interfaces(dir):

    clus: dict[int, list[CluInterface]] = {}
    modules: dict[int, list[ModuleInterface]] = {}
    objects: dict[int, list[CluObjectInterface]] = {}

    for filename in os.scandir(dir):
        if filename.is_file():
            try:
                with open(filename, "r") as file:
                    if filename.name.startswith("clu_"):
                        clu = parse_clu_xml(file)
                        _append_elm(clus, clu.hw_type, clu)

                    elif filename.name.startswith("module_"):
                        mod = parse_clu_xml(file)
                        _append_elm(modules, mod.hw_type, mod)

                    elif filename.name.startswith("object_"):
                        obj = parse_clu_xml(file)
                        _append_elm(obj, obj.hw_type, obj)

            except IOError:
                pass

    for k, v in clus.items():
        v.sort(key=lambda x: x.fw_api_version)

    for k, v in modules.items():
        v.sort(key=lambda x: x.fw_api_version)

    for k, v in objects.items():
        v.sort(key=lambda x: x.version)

    return clus, modules, objects
