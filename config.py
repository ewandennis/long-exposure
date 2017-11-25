from strictyaml import load, Map, Bool, Str, Float, Int

class Config:
    SCHEMA = Map(dict(
        image_scale=Float(),
        frame_limit=Int(),
        dump_stats=Bool(),
        alignment=Map(dict(enabled=Bool(), mode=Str(), max_iterations=Int(), termination_eps=Float()))
    ))

    def __init__(self, file_or_yaml=open('config.yaml', 'r')):
        if isinstance(file_or_yaml, str):
            yaml_str = file_or_yaml
        else:
            yaml_str = file_or_yaml.read()
            file_or_yaml.close()
        self.cfg = load(yaml_str, Config.SCHEMA).data

    def get(self, key):
        return self.cfg[key]

