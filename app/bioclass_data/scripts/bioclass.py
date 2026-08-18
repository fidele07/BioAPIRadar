import os
import numpy as np
import zarr
from datetime import datetime, timezone
from .bio_info import get_class_info
from app.scripts.util import (
        decode_fill_value,
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.imagepng import bioclass_imagePng

def download_bioclass(params):
    """Classification frame rendered from the bioclass store.

    Reads the store directly with zarr: the xarray/dask path built a
    per-request task graph over every chunk of the ever-growing store
    (per-timestep chunking -> hundreds of thousands of chunks), which
    ballooned uWSGI workers to 7-11 GB per request under the frame
    preloader and OOM-killed the service. A direct read touches only
    the requested timestep (~8 MB per level, ~170 MB for a composite).
    """
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
    param_info = get_class_info(params['class'])
    arr = store[param_info['field']]
    fill = decode_fill_value(dict(arr.attrs))
    # height < 0 requests the column composite: the class maximum over
    # all heights (a gate is Bird/Biological if any level says so)
    composite = hgt_req < 0
    if composite:
        z_label = 'Composite (max)'
        class_data = np.asarray(arr[it], dtype='float64')
        if fill is not None:
            class_data[class_data == fill] = np.nan
        with np.errstate(invalid='ignore'):
            class_data = np.nanmax(class_data, axis=0)
    else:
        iz = int(np.abs(height - hgt_req).argmin())
        z_label = f'{height[iz]} m'
        class_data = np.asarray(arr[it, iz], dtype='float64')
        if fill is not None:
            class_data[class_data == fill] = np.nan
    data = {
        'lon': store['lon'][:],
        'lat': store['lat'][:],
        'data': class_data
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
                    'height': z_label,
                    'name': param_info['name'],
                    'class': params['class']
                }
    return response_download_json(out, 'class_data')
