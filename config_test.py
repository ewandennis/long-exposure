import unittest
from config import Config
import strictyaml

class ReadConfigTest(unittest.TestCase):
    YAML_STR = '''image_scale: 0.5
frame_limit: 5
alignment:
  enabled: true
  mode: homography
  max_iterations: 100
  termination_eps: 1e-10
dump_stats: false
'''

    def test_accepts_files(self):
        file = open('test.yaml', 'r')
        cfg = Config(file)

    def test_accepts_strings(self):
        cfg = Config(ReadConfigTest.YAML_STR)

    def test_validates_yaml(self):
        bad_yaml = ReadConfigTest.YAML_STR + '\nfredo: on-a-boat\n'
        with self.assertRaises(strictyaml.exceptions.YAMLValidationError):
            Config(bad_yaml)

class AccessConfigTest(unittest.TestCase):
    def test_get(self):
        cfg = Config(open('test.yaml', 'r'))
        alignment_enabled = cfg.get('alignment')['enabled']
        self.assertIsInstance(alignment_enabled, bool)

