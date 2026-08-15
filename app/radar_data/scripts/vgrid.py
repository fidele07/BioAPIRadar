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
        response_download_error,
        response_download_image
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.vcross import (
        compute_vcross_grid,
        vcross_format_params
    )
from app.scripts.imagepng import vcross_imagePng

def vcross_section_grid(params):
    pars = vcross_format_params(params)
    file = 'vertical_cross_sec_grid'
    if pars['status'] == -1:
        return response_download_error(
                pars['message'], file, 422
            )
    out = _vcross_section_grid(pars['params'])
    if out is None:
        msg = 'Zarr data not found.'
        return response_download_error(
                msg, file, 422
            )
    return response_download_json(out, file)

def image_vcross_section_grid(params):
    pars = vcross_format_params(params)
    file = 'vertical_cross_sec_grid'
    if pars['status'] == -1:
        return response_download_error(
                pars['message'], file, 422
            )
    vcross = _vcross_section_grid(pars['params'])
    if vcross is None:
        msg = 'Zarr data not found.'
        return response_download_error(
                msg, file, 422
            )
    img_png = vcross_imagePng(
        vcross, color_name=params['colorbar']
    )
    return response_download_image(
                img_png, file, 'png'
            )

def _vcross_section_grid(params):
    zarr_info = GLOBAL_CONFIG['grid']
    zarr_dirfile = zarr_info['file'] % (params['radarID'])
    zarr_path = os.path.join(
        zarr_info['dir'], zarr_dirfile
    )
    if not os.path.exists(zarr_path):
        return None

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
    ds_t = ds.isel(time=it)
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

    lon = ds_t.lon.values
    lat = ds_t.lat.values
    hgt = ds_t.z.values

    out = compute_vcross_grid(
        params, data, lon, lat, hgt
    )
    out['info'] = {
        'time': time_out,
        'name': param_info['name'],
        'units': param_info['units'],
        'type': params['type']
    }
    return out
