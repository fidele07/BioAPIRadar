import os
import netCDF4 as nc
import numpy as np
import xarray as xr
from datetime import datetime
from .rinfo import get_field_info
from app.scripts.util import (
            open_zarr_retry,
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
    # height < 0 requests the column composite (maximum over all heights)
    composite = hgt_req < 0
    if composite:
        ds_t = ds.isel(time=it)
        z_label = 'Composite (max)'
    else:
        iz = min(range(len(height)), key=lambda i: abs(height[i] - hgt_req))
        z_label = f'{height[iz]} m'
        ds_t = ds.isel(time=it, z=iz)
    param_info = get_field_info(params['parameter'])

    if params['parameter'] == 'dr':
        zdr_info = get_field_info('zdr')
        zdr = ds_t[zdr_info['field']].values
        rho_info = get_field_info('rho')
        rho = ds_t[rho_info['field']].values
        # DR formula requires LINEAR differential reflectivity; ZDR is
        # stored in dB (negative values are common for biology)
        zdr_lin = 10.0 ** (zdr / 10.0)
        num = 1 + zdr_lin - 2 * (zdr_lin**0.5) * rho
        den = 1 + zdr_lin + 2 * (zdr_lin**0.5) * rho
        data = 10 * np.log10(num / den)
    else:
        data = ds_t[param_info['field']].values
    if composite:
        data = np.nanmax(data, axis=0)

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
                    'height': z_label,
                    'name': param_info['name'],
                    'units': param_info['units'],
                    'type': params['type']
                }
    return response_download_json(img_obj, 'grid_data')
