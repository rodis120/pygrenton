
import os
import re
import xml.dom.minidom as md
from xml.dom.minidom import Element

from ..interfaces import *

VALUE_RANGE_TEMPLATE = re.compile(r"\d+\s*-\s*\d+")

def _parse_feature(elm: Element) -> FeatureInterface:
    name = elm.getAttribute("name")
    index = int(elm.getAttribute("index"))
    get = elm.getAttribute("get") == "true"
    set = elm.getAttribute("set") == "true"
    data_type = DataType(elm.getAttribute("type")) #TODO: make data type more generic
    unit = elm.getAttribute("unit")

    value_range = None
    vr = elm.getAttribute("range")
    if VALUE_RANGE_TEMPLATE.match(vr):
        value_range = tuple(int(x) for x in elm.getAttribute("range").split("-"))

    enum = None
    en = elm.getAttribute("enum")
    if en != "":
        if data_type == DataType.STRING:
            enum = {s: None for s in elm.getAttribute("enum").split(",")}
        elif data_type == DataType.NUMBER:
            enum = {int(s): None for s in elm.getAttribute("enum").split(",")}
            
        for node in elm.getElementsByTagName("enum"):
            name = node.getAttribute("name")
            value = node.getAttribute("value")
            enum[value] = name

    return FeatureInterface(name, index, get, set, data_type, unit, enum, value_range)

def _parse_parameter(elm: Element) -> ParameterInterface:
    name = elm.getAttribute("name")
    data_type = DataType(elm.getAttribute("type"))
    unit = elm.getAttribute("unit")

    value_range = None
    vr = elm.getAttribute("range")
    if VALUE_RANGE_TEMPLATE.match(vr):
        value_range = tuple(int(x) for x in elm.getAttribute("range").split("-"))

    enum = None
    en = elm.getAttribute("enum")
    if en != "":
        if data_type == DataType.STRING:
            enum = [s for s in elm.getAttribute("enum").split(",")]
        elif data_type == DataType.NUMBER:
            enum = [int(s) for s in elm.getAttribute("enum").split(",")]

    return ParameterInterface(name, data_type, unit, enum, value_range)

def _parse_method(elm: Element) -> MethodInterface:
    call = CallType(elm.getAttribute("call"))
    index = int(elm.getAttribute("index"))
    name = elm.getAttribute("name")

    # make return type more generic
    return_value = DataType(elm.getAttribute("return"))

    params = [_parse_parameter(par) for par in elm.getElementsByTagName("param")]

    return MethodInterface(name, index, call, return_value, None, params)

def _parse_module_object(xml: Element) -> ModuleObjectInterface:

    obj_class = int(xml.getAttribute("class"))
    name = xml.getAttribute("name")
    obj_type = ModuleObjectType(xml.getAttribute("type"))

    features = [_parse_feature(x) for x in xml.getElementsByTagName("feature")]
    methods = [_parse_method(x) for x in xml.getElementsByTagName("method")]

    return ModuleObjectInterface(name, obj_class, obj_type, features, methods)

def parse_clu_object_xml(file) -> CluObjectInterface:
    dom = md.parse(file)

    obj = dom.getElementsByTagName("object")[0]
    obj_class = int(obj.getAttribute("class"))
    name = obj.getAttribute("name")
    version = int(obj.getAttribute("version"))

    features = [_parse_feature(xml) for xml in dom.getElementsByTagName("feature")]
    methods = [_parse_method(xml) for xml in dom.getElementsByTagName("method")]

    return CluObjectInterface(name, obj_class, version, features, methods)

def parse_module_xml(file) -> ModuleInterface:
    dom = md.parse(file)

    mod = dom.getElementsByTagName("module")[0]
    name = mod.getAttribute("name")
    hw_type = int(mod.getAttribute("typeId"), 16)

    fw = dom.getElementsByTagName("firmware")[0]
    fw_type = int(fw.getAttribute("typeId"), 16)
    fw_api_version = int(fw.getAttribute("version"), 16)

    objects = {}

    for obj_xml in dom.getElementsByTagName("object"):
        obj = _parse_module_object(obj_xml)
        objects[obj.obj_class] = obj

    return ModuleInterface(name, hw_type, fw_type, fw_api_version, objects)

def parse_clu_xml(file, objects_repo: dict[str, list[CluObjectInterface]]) -> CluInterface:
    dom = md.parse(file)

    clu = dom.getElementsByTagName("CLU")[0]
    name = clu.getAttribute("typeName")
    hw_type = int(clu.getAttribute("hardwareType"), 16)
    hw_version = int(clu.getAttribute("hardwareVersion"), 16)
    fw_type = int(clu.getAttribute("firmwareType"), 16)
    fw_version = int(clu.getAttribute("firmwareVersion"), 16)

    features = [_parse_feature(x) for x in dom.getElementsByTagName("feature")]
    methods = [_parse_method(x) for x in dom.getElementsByTagName("method")]

    objects = {}
    for obj in dom.getElementsByTagName("object"):
        obj_name = obj.getAttribute("name")
        obj_version = int(obj.getAttribute("version"))
        
        for obj_int in objects_repo[obj_name]:
            if obj_int.version == obj_version:
                objects[obj_int.obj_class] = obj_int

    return CluInterface(name, hw_type, hw_version, fw_type, fw_version, features, methods, objects)

def _append_elm(dict: dict, key, val):
    if key in dict:
        dict[key].append(val)
    else:
        dict[key] = [val]

def parse_interfaces(dir):

    clus: dict[int, list[CluInterface]] = {}
    modules: dict[int, list[ModuleInterface]] = {}
    objects: dict[str, list[CluObjectInterface]] = {}

    for path in os.scandir(dir):
        if not path.is_file() or not path.name.startswith("object_"):
            continue
        
        try:
            with open(path, 'r', encoding="utf-8") as file:
                obj = parse_clu_object_xml(file)
                _append_elm(objects, obj.name, obj)
        except IOError:
            pass

    for path in os.scandir(dir):
        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as file:
                    if path.name.startswith("clu_"):
                        clu = parse_clu_xml(file, objects)
                        _append_elm(clus, clu.hw_type, clu)

                    elif path.name.startswith("module_"):
                        mod = parse_module_xml(file)
                        _append_elm(modules, mod.hw_type, mod)

            except IOError:
                pass

    for _, v in clus.items():
        v.sort(key=lambda x: x.fw_api_version)

    for _, v in modules.items():
        v.sort(key=lambda x: x.fw_api_version)

    return clus, modules
