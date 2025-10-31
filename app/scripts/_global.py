import os
# import config
from .util import load_yaml_file

GLOBAL_CONFIG = {}
scripts_dir = os.path.dirname(os.path.realpath(__file__))
app_dir = os.path.dirname(scripts_dir)
GLOBAL_CONFIG['app_dir'] = app_dir

config_data_file = os.path.join(app_dir, 'yaml', 'datasets-config.yaml')
GLOBAL_CONFIG.update(load_yaml_file(config_data_file))
