import os
import sys

os.environ['RPY2_CFFI_MODE'] = 'ABI'
rm_mod = [mod for mod in sys.modules if mod.startswith('rpy2')]
for mod in rm_mod:
	del sys.modules[mod] 

### 
from flask import Flask
from flask_cors import CORS

app = Flask(__name__, instance_relative_config = False)
app.config.from_object('config')
CORS(app)

###
import config
import tempfile

os.environ['MPLCONFIGDIR'] = tempfile.mkdtemp()
# os.environ['R_HOME'] = config.R_HOME
# os.environ['R_LIBS_SITE'] = config.R_LIBS_SITE

### 
from app.biorad_data.index import biorad_data
from app.radar_data.index import radar_data
from app.bioclass_data.index import bioclass_data

app.register_blueprint(biorad_data)
app.register_blueprint(radar_data)
app.register_blueprint(bioclass_data)

