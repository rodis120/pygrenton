
class GFeature:
    pass

class GMethod:
    pass

class GObject:
    name: str
    unique_id: str
    obj_type: int

    features: list
    methods: list

class GModule:
    
    objects: list[GObject]

class GCLU:
    pass