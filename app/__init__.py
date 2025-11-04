import os
import sys
import tempfile

os.environ['RPY2_CFFI_MODE'] = 'ABI'
rm_mod = [mod for mod in sys.modules if mod.startswith('rpy2')]
for mod in rm_mod:
    del sys.modules[mod] 

os.environ['MPLCONFIGDIR'] = tempfile.mkdtemp()

### 
from flask import Flask
from flask_cors import CORS

app = Flask(__name__, instance_relative_config = False)
app.config.from_object('config')
CORS(app)

###
import config

from app.scripts.util import response_download_data
from app.scripts.geojson import (
                            get_map_geojson,
                            get_attr_geojson
                        )
### 
from app.biorad_data.index import biorad_data
from app.radar_data.index import radar_data
from app.bioclass_data.index import bioclass_data

app.register_blueprint(biorad_data)
app.register_blueprint(radar_data)
app.register_blueprint(bioclass_data)

### 
@app.route('/data_geojson', methods=['GET', 'POST'])
def data_geojson():
    return response_download_data(get_map_geojson)

@app.route('/attr_geojson', methods=['GET', 'POST'])
def attr_geojson():
    return response_download_data(get_attr_geojson)

