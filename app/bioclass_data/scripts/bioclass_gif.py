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
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagegif import bioclass_animeGif

def anime_gif_bioclass(params):
    zarr_info = GLOBAL_CONFIG['class']
    zarr_dirfile = zarr_info['file'] % (params['radarID'])
    zarr_path = os.path.join(
        zarr_info['dir'], zarr_dirfile
    )
    if not os.path.exists(zarr_path):
        msg = 'Zarr data not found.'
        return response_download_error(
                msg, 'class_data_gif', 422
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
    start_time = datetime.strptime(
        params['startTime'], format_time
    )
    end_time = datetime.strptime(
        params['endTime'], format_time
    )
    it = [
        i for i, t in enumerate(time)
        if start_time <= t <= end_time
    ]
    if len(it) == 0:
        msg = 'No data found.'
        return response_download_error(
                msg, 'class_data_gif', 422
            )
    times = [time[i] for i in it]
    height = ds.z.values
    hgt_req = float(params['height'])
    iz = min(range(len(height)), key=lambda i: abs(height[i] - hgt_req))
    z_out = height[iz]
    ds_t = ds.isel(time=it, z=iz)
    lon = ds_t.lon.values
    lat = ds_t.lat.values
    param_info = get_class_info(params['class'])
    data = ds_t[param_info['field']].values

    ix_time = list(enumerate(times))
    ix_time = sorted(ix_time, key=lambda x: x[1])
    times = [x[1] for x in ix_time]
    ix = [x[0] for x in ix_time]
    data = data[ix, :, :]
    data = np.ma.masked_invalid(data)
    data = {
            'lon': lon, 'lat': lat,
            'times': times, 'frames': data
        }
    gif_obj = bioclass_animeGif(data,
                     color_0=params['color_0'],
                     color_1=params['color_1'])

    out = {'data': gif_obj}
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
    times_info = [t.strftime('%Y-%m-%d %H:%M:%S') for t in times]
    out['info'] = {
                    'time': times_info,
                    'height': f'{z_out} m',
                    'name': param_info['name'],
                    'class': params['class']
                }
    return response_download_json(out, 'class_data_gif')
