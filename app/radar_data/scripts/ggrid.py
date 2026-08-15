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
from app.scripts.imagegif import create_animeGif

def anime_gif_grid(params):
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
                msg, 'grid_data_gif', 422
            )
    times = [time[i] for i in it]
    height = ds.z.values
    hgt_req = float(params['height'])
    iz = min(range(len(height)), key=lambda i: abs(height[i] - hgt_req))
    z_out = height[iz]
    ds_t = ds.isel(time=it, z=iz)
    lon = ds_t.lon.values
    lat = ds_t.lat.values
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
    gif_obj = create_animeGif(data, color_name=params['colorbar'])
    times_info = [t.strftime('%Y-%m-%d %H:%M:%S') for t in times]
    gif_obj['info'] = {
                    'time': times_info,
                    'height': f'{z_out} m',
                    'name': param_info['name'],
                    'units': param_info['units'],
                    'type': params['type']
                }
    return response_download_json(gif_obj, 'grid_data_gif')
