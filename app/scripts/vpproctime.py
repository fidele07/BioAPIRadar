import os
import config
import rpy2.robjects as robjects
from rpy2.robjects import ListVector
from rpy2.robjects import conversion, default_converter
from .util import (
        response_download_error,
        response_download_image
    )

def get_vp_proctime_image(params):
    params['bioradar_dir'] = config.BIORADAR_DIR
    script_file = os.path.join(
            config.BIORADAR_DIR, 'scripts', 'vp_proc_time.R'
        )
    with conversion.localconverter(default_converter):
        rparams = ListVector(params)
        robjects.r.source(script_file)
        robj = robjects.r.vp_processing_time(rparams)
        pyobj = {key : robj.rx2(key)[0] for key in robj.names}

    if pyobj['status'] == -1:
        return response_download_error(
                pyobj['message'], vp_file, 422
            )
    return response_download_image(
                pyobj['data'], 'vp_processing_time', 'png'
            )
