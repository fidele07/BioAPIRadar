import os
import numpy as np
import zarr
from datetime import datetime, timezone
from .rinfo import get_field_info
from app.scripts.util import (
        decode_fill_value,
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagepng import create_imagePng

def _read_field(store, field, it, iz, fill):
    """One timestep (level or full column) of a field, fill masked to NaN.
    Direct zarr read — the xarray/dask path built per-request task graphs
    over every chunk of the growing store and OOM-killed workers."""
    arr = store[field]
    if iz is None:
        data = np.asarray(arr[it], dtype='float64')
    else:
        data = np.asarray(arr[it, iz], dtype='float64')
    f = fill if fill is not None else decode_fill_value(dict(arr.attrs))
    if f is not None:
        data[data == f] = np.nan
    return data

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
    store = zarr.open_group(zarr_path, mode='r')
    # time stored as epoch seconds (data_grid_time_encoding)
    time_s = store['time'][:].astype('int64')
    format_time = '%Y-%m-%d %H:%M:%S'
    t_req = int(
        datetime.strptime(params['time'], format_time)
        .replace(tzinfo=timezone.utc).timestamp()
    )
    it = int(np.abs(time_s - t_req).argmin())
    time_out = datetime.fromtimestamp(
        int(time_s[it]), tz=timezone.utc
    ).strftime(format_time)
    height = store['z'][:]
    hgt_req = float(params['height'])
    # height < 0 requests the column composite (maximum over all heights)
    composite = hgt_req < 0
    if composite:
        iz = None
        z_label = 'Composite (max)'
    else:
        iz = int(np.abs(height - hgt_req).argmin())
        z_label = f'{height[iz]} m'
    param_info = get_field_info(params['parameter'])

    if params['parameter'] == 'dr':
        zdr = _read_field(store, get_field_info('zdr')['field'], it, iz, None)
        rho = _read_field(store, get_field_info('rho')['field'], it, iz, None)
        # DR formula requires LINEAR differential reflectivity; ZDR is
        # stored in dB (negative values are common for biology)
        zdr_lin = 10.0 ** (zdr / 10.0)
        num = 1 + zdr_lin - 2 * (zdr_lin**0.5) * rho
        den = 1 + zdr_lin + 2 * (zdr_lin**0.5) * rho
        with np.errstate(invalid='ignore', divide='ignore'):
            data = 10 * np.log10(num / den)
    else:
        data = _read_field(store, param_info['field'], it, iz, None)
    if composite:
        with np.errstate(invalid='ignore'):
            data = np.nanmax(data, axis=0)

    data = {
        'lon': store['lon'][:],
        'lat': store['lat'][:],
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
