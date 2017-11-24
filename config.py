from strictyaml import load, Map, Str, Float, Int

class Config:
    SCHEMA = Map(dict(
        image_scale=Float(),
        frame_limit=Int(),
        alignment=Map(dict(mode=Str(), termination_iterations=Int(), termination_eps=Float()))
    ))
    def __init__(self, path='config.yaml'):
        yaml_str = open(path, 'r').read()
        self.cfg = load(yaml_str, Config.SCHEMA).data

    def get(self, key):
        return self.cfg[key]

