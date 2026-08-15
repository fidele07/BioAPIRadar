import os
import netCDF4 as nc
import numpy as np
import xarray as xr
from datetime import datetime
from .bio_info import get_class_info
from app.scripts.util import (
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
from app.scripts.imagepng import vbioclass_imagePng

def get_vcross_bioclass(params):
    pars = vcross_format_params(params)
    file = 'vertical_cross_sec_bio'
    if pars['status'] == -1:
        return response_download_error(
                pars['message'], file, 422
            )
    out = _vcross_section_bioclass(pars['params'])
    if out is None:
        msg = 'Zarr data not found.'
        return response_download_error(
                msg, file, 422
            )
    return response_download_json(out, file)

def image_vcross_bioclass(params):
    pars = vcross_format_params(params)
    file = 'vertical_cross_sec_bio'
    if pars['status'] == -1:
        return response_download_error(
                pars['message'], file, 422
            )
    vcross = _vcross_section_bioclass(pars['params'])
    if vcross is None:
        msg = 'Zarr data not found.'
        return response_download_error(
                msg, file, 422
            )
    img_png = vbioclass_imagePng(
        vcross,
        color_0=params['color_0'],
        color_1=params['color_1']
    )
    return response_download_image(
                img_png, file, 'png'
            )

def _vcross_section_bioclass(params):
    zarr_info = GLOBAL_CONFIG['class']
    zarr_dirfile = zarr_info['file'] % (params['radarID'])
    zarr_path = os.path.join(
        zarr_info['dir'], zarr_dirfile
    )
    if not os.path.exists(zarr_path):
        return None

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
    ds_t = ds.isel(time=it)
    param_info = get_class_info(params['class'])

    data = ds_t[param_info['field']].values
    lon = ds_t.lon.values
    lat = ds_t.lat.values
    hgt = ds_t.z.values

    out = compute_vcross_grid(
        params, data, lon, lat, hgt
    )
    vcross = np.array(out['vcross'], dtype=float)
    class_0 = vcross <= 0.5
    class_1 = vcross > 0.5 
    vcross[class_0] = 0
    vcross[class_1] = 1
    vcross = np.where(np.isnan(vcross), None, vcross)
    out['vcross'] = vcross.tolist()
    if params['class'] == 'biometeo':
        category = ['Meteorological', 'Biological']
    else:
        category = ['Insect', 'Bird']
    out['info'] = {
        'time': time_out,
        'name': param_info['name'],
        'class': params['class'],
        'level': [0, 1],
        'category': category
    }
    return out
