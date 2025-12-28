import os
import xarray as xr
from datetime import datetime
from app.scripts.util import (
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagepng import create_imagePng

def get_sevip_json(params):
    zarr_info = GLOBAL_CONFIG['vertical']['zarr']
    zarr_dirfile = zarr_info['file'] % (params['radarID'])
    zarr_path = os.path.join(
        zarr_info['dir'], zarr_dirfile
    )
    if not os.path.exists(zarr_path):
        msg = 'Zarr data not found.'
        return response_download_error(
                msg, 'sevip_data', 422
            )
    ds = xr.open_zarr(
        zarr_path, consolidated=False
    )
    time = ds.time.values
    time = time.astype('datetime64[s]')
    time = time.astype(datetime)
    format_time = '%Y-%m-%d %H:%M:%S'
    time_req = datetime.strptime(params['time'], format_time)
    it = min(range(len(time)), key=lambda i: abs(time[i] - time_req))
    ds_t = ds.isel(time=it)
    species = 1 if params['species'] == 'bird' else 0
    ds_t = ds_t.sel(species=species)
    data = {
        'lon': ds_t.lon.values,
        'lat': ds_t.lat.values,
        'data': ds_t[params['parameter']].values
    }
    img_obj = create_imagePng(data, color_name=params['colorbar'])
    var_time = ds_t.time.values
    var_time = var_time.astype('datetime64[s]')
    var_time = var_time.astype(datetime)
    img_obj['info'] = {
                    'time': var_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'name': ds_t[params['parameter']].long_name,
                    'units': ds_t[params['parameter']].units
                }
    return response_download_json(img_obj, 'sevip_data')
