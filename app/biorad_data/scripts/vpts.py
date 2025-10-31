import json
from app.scripts.util import (
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG

from rpy2.robjects.packages import importr
from rpy2.robjects import ListVector
import rpy2.robjects as robjects
from rpy2.robjects import conversion, default_converter

biorad = importr('BioVPRadar')

def download_vp(params):
    data_dir = GLOBAL_CONFIG['vp']['dir']
    with conversion.localconverter(default_converter):
        rparams = ListVector(params)
        robj = biorad.get_vp(data_dir, rparams)
        pyobj = {key : robj.rx2(key)[0] for key in robj.names}

    if 'data' in pyobj:
        pyobj['data'] = json.loads(pyobj['data'])

    if pyobj['status'] == -1:
        return response_download_error(
                pyobj['message'], 'vp_data', 422
            )

    return response_download_json(pyobj, params, 'vp_data')

def download_vpts(params):
    data_dir = GLOBAL_CONFIG['vp']['dir']
    with conversion.localconverter(default_converter):
        rparams = ListVector(params)
        robj = biorad.get_vpts(data_dir, rparams)
        pyobj = {key : robj.rx2(key)[0] for key in robj.names}

    if 'data' in pyobj:
        pyobj['data'] = json.loads(pyobj['data'])

    if pyobj['status'] == -1:
        return response_download_error(
                pyobj['message'], 'vpts_data', 422
            )

    return response_download_json(pyobj, params, 'vpts_data')

def download_vtip(params):
    data_dir = GLOBAL_CONFIG['vp']['dir']
    with conversion.localconverter(default_converter):
        rparams = ListVector(params)
        robj = robjects.r['get_vtip'](data_dir, rparams)
        # robj = biorad.get_vtip(data_dir, rparams)
        pyobj = {key : robj.rx2(key)[0] for key in robj.names}

    if 'data' in pyobj:
        pyobj['data'] = json.loads(pyobj['data'])

    if pyobj['status'] == -1:
        return response_download_error(
                pyobj['message'], 'vtip_data', 422
            )

    return response_download_json(pyobj, params, 'vtip_data')

