import json
from app.scripts.util import (
        response_download_json,
        response_download_error,
        response_download_image
    )
from app.scripts._global import GLOBAL_CONFIG

import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
from rpy2.robjects import ListVector
from rpy2.robjects import conversion, default_converter

biorad = importr('BioVPRadar')

def download_vp(params):
    return _download_vp_data(
                params, 'get_vp', 'vp_data'
            )

def download_vpts(params):
    return _download_vp_data(
                params, 'get_vpts', 'vpts_data'
            )

def download_vtip(params):
    return _download_vp_data(
                params, 'get_vtip', 'vtip_data'
            )

def _download_vp_data(params, vp_fun, vp_file):
    vp_info = GLOBAL_CONFIG['vertical']['vp']
    with conversion.localconverter(default_converter):
        vp_info = ListVector(vp_info)
        rparams = ListVector(params)
        robj = robjects.r[vp_fun](vp_info, rparams)
        pyobj = {key : robj.rx2(key)[0] for key in robj.names}

    if pyobj['status'] == -1:
        return response_download_error(
                pyobj['message'], vp_file, 422
            )
    if 'data' in pyobj:
        pyobj['data'] = json.loads(pyobj['data'])

    return response_download_json(pyobj['data'], vp_file)

def get_vpts_image(params):
    vp_info = GLOBAL_CONFIG['vertical']['vp']
    with conversion.localconverter(default_converter):
        vp_info = ListVector(vp_info)
        rparams = ListVector(params)
        robj = biorad.get_vpts_image(vp_info, rparams)
        pyobj = {key : robj.rx2(key)[0] for key in robj.names}

    if pyobj['status'] == -1:
        return response_download_error(
                pyobj['message'], vp_file, 422
            )
    return response_download_image(
                pyobj['data'], 'vpts_image', 'png'
            )

def get_vtip_image(params):
    vp_info = GLOBAL_CONFIG['vertical']['vp']
    with conversion.localconverter(default_converter):
        vp_info = ListVector(vp_info)
        rparams = ListVector(params)
        robj = biorad.get_vtip_image(vp_info, rparams)
        pyobj = {key : robj.rx2(key)[0] for key in robj.names}

    if pyobj['status'] == -1:
        return response_download_error(
                pyobj['message'], vp_file, 422
            )
    return response_download_image(
                pyobj['data'], 'vtip_image', 'png'
            )
