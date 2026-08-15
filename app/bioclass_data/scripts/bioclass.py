import os
import netCDF4 as nc
import numpy as np
import xarray as xr
from datetime import datetime
from .bio_info import get_class_info
from app.scripts.util import (
            open_zarr_retry,
        data_grid_time_encoding,
        cftime2datetime,
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagepng import bioclass_imagePng

def download_bioclass(params):
    zarr_info = GLOBAL_CONFIG['class']
    zarr_dirfile = zarr_info['file'] % (params['radarID'])
    zarr_path = os.path.join(
        zarr_info['dir'], zarr_dirfile
    )
    if not os.path.exists(zarr_path):
        msg = 'Zarr data not found.'
        return response_download_error(
                msg, 'class_data', 422
            )
    ds = open_zarr_retry(zarr_path)
    time_encoding = data_grid_time_encoding()
    time = nc.num2date(
        ds.time.values,
        units=time_encoding['units'],
        calendar=time_encoding['calendar']
    )
    time = [cftime2datetime(t) for t in time]
    format_time = '%Y-%m-%d %H:%M:%S'
    time_req = datetime.strptime(params['time'], format_time)
    it = min(range(len(time)), key=lambda i: abs(time[i] - time_req))
    time_out = time[it].strftime(format_time)
    height = ds.z.values
    hgt_req = float(params['height'])
    iz = min(range(len(height)), key=lambda i: abs(height[i] - hgt_req))
    z_out = height[iz]
    ds_t = ds.isel(time=it, z=iz)
    param_info = get_class_info(params['class'])
    data = {
        'lon': ds_t.lon.values,
        'lat': ds_t.lat.values,
        'data': ds_t[param_info['field']].values
    }
    img_obj = bioclass_imagePng(
        data,
         color_0=params['color_0'],
         color_1=params['color_1']
    )
    out = {'data': img_obj}
    out['legend'] = {
            'class_0': {
                'name': param_info['class_0'],
                'color': params['color_0']
            },
            'class_1': {
                'name': param_info['class_1'],
                'color': params['color_1']
            }
        }
    out['info'] = {
                    'time': time_out,
                    'height': f'{z_out} m',
                    'name': param_info['name'],
                    'class': params['class']
                }
    return response_download_json(out, 'class_data')
