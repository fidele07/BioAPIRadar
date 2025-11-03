import os
import json
from app.scripts.netcdf import read_netcdf_nc
from app.scripts.util import (
        get_data_file_path,
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagepng import create_imagePng

def download_sevip(params):
    data_info = GLOBAL_CONFIG['vertical']['sevip']
    nc_path = get_data_file_path(data_info, params['time'])
    if nc_path is None:
        msg = 'No data found.'
        return response_download_error(
                msg, 'sp_vertically_integrated', 422
            )
    data = read_netcdf_nc(
                nc_path, params['parameter'],
                GLOBAL_CONFIG['vertical']['sevip']
            )
    img_obj = create_imagePng(data, color_name=params['colorbar'])
    img_obj['info'] = {
                    'time': data['time'].strftime('%Y-%m-%d %H:%M:%S'),
                    'name': data['name'], 'units': data['units']
                }
    return response_download_json(img_obj, 'sevip_data')
