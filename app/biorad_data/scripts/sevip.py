import os
import glob
import json
from datetime import datetime, timedelta
from app.scripts.netcdf import read_netcdf_nc
from app.scripts.util import (
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagepng import create_imagePng

def download_sevip(params):
    nc_path = _get_sevip_file_path(params['time'])
    if nc_path is None:
        msg = 'No data found.'
        return response_download_error(
                msg, 'sp_vertically_integrated', 422
            )
    data = read_netcdf_nc(
                nc_path, params['parameter'],
                GLOBAL_CONFIG['vp']['sevip']
            )
    img_obj = create_imagePng(data, color_name=params['colorbar'])
    img_obj['info'] = {
                    'time': data['time'].strftime('%Y-%m-%d %H:%M:%S'),
                    'name': data['name'], 'units': data['units']
                }
    return response_download_json(img_obj, params, 'sevip_data')

def _get_sevip_file_path(time_str):
    format_time = '%Y-%m-%d %H:%M:%S'
    format_dir = '%Y-%m-%d'
    format_file = 'vid_%Y%m%d%H%M%S.nc'
    pattern = 'vid_*.nc'
    data_dir = GLOBAL_CONFIG['vp']['dir']
    time_req = datetime.strptime(time_str, format_time)
    date_dir = time_req.strftime(format_dir)
    data_dir = os.path.join(data_dir, 'vid', date_dir)
    if not os.path.isdir(data_dir):
        return None
    data_files = glob.glob(f'{data_dir}/{pattern}')
    data_files = [os.path.basename(p) for p in data_files]
    date_files = [datetime.strptime(f, format_file) for f in data_files]
    date = min(date_files, key=lambda dt: abs(dt - time_req))
    file = date.strftime(format_file)
    return os.path.join(data_dir, file)
