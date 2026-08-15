import os
import netCDF4 as nc
import numpy as np
import xarray as xr
from datetime import datetime
from .rinfo import get_field_info
from app.scripts.util import (
        data_grid_time_encoding,
        cftime2datetime,
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagepng import create_imagePng

def download_grid(params):
    zarr_info = GLOBAL_CONFIG['grid']
    zarr_dirfile = zarr_info['file'] % (params['radarID'])
    zarr_path = os.path.join(
        zarr_info['dir'], zarr_dirfile
    )
    if not os.path.exists(zarr_path):
        msg = 'Zarr data not found.'
        return response_download_error(
                msg, 'grid_data', 422
            )
    ds = xr.open_zarr(
        zarr_path, consolidated=True
    )
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
    param_info = get_field_info(params['parameter'])

    if params['parameter'] == 'dr':
        zdr_info = get_field_info('zdr')
        zdr = ds_t[zdr_info['field']].values
        rho_info = get_field_info('rho')
        rho = ds_t[rho_info['field']].values
        num = 1 + zdr - 2 * (zdr**0.5) * rho
        den = 1 + zdr + 2 * (zdr**0.5) * rho
        data = 10 * np.log10(num / den)
    else:
        data = ds_t[param_info['field']].values

    data = {
        'lon': ds_t.lon.values,
        'lat': ds_t.lat.values,
        'data': data
    }
    img_obj = create_imagePng(
        data, color_name=params['colorbar']
    )
    img_obj['info'] = {
                    'time': time_out,
                    'height': f'{z_out} m',
                    'name': param_info['name'],
                    'units': param_info['units'],
                    'type': params['type']
                }
    return response_download_json(img_obj, 'grid_data')
