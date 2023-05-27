
from config_json_parser import parse_json
from om_parser import parse_om
from modules import IO_Module

def parse_clu_config(json_confg, om_config):
    clu = parse_json(json_confg)
    names, io_modules, objects = parse_om(om_config)
    

