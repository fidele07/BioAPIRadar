import os
import numpy as np
import zarr
from .rinfo import get_field_info
from app.scripts.util import (
        zarr_nearest_time,
        zarr_read_timestep,
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

    store = zarr.open_group(zarr_path, mode='r')
    it, time_out = zarr_nearest_time(store, params['time'])
    param_info = get_field_info(params['parameter'])

    if params['parameter'] == 'dr':
        zdr = zarr_read_timestep(store, get_field_info('zdr')['field'], it)
        rho = zarr_read_timestep(store, get_field_info('rho')['field'], it)
        # DR formula requires LINEAR differential reflectivity; ZDR is
        # stored in dB (sqrt of negative dB values silently masked the
        # bird-typical gates)
        zdr_lin = 10.0 ** (zdr / 10.0)
        num = 1 + zdr_lin - 2 * (zdr_lin**0.5) * rho
        den = 1 + zdr_lin + 2 * (zdr_lin**0.5) * rho
        with np.errstate(invalid='ignore', divide='ignore'):
            data = 10 * np.log10(num / den)
    else:
        data = zarr_read_timestep(store, param_info['field'], it)

    lon = store['lon'][:]
    lat = store['lat'][:]
    hgt = store['z'][:]

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
