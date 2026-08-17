import base64
import os
import struct
from datetime import datetime, timezone

import numpy as np
import zarr
from matplotlib.path import Path

from app.scripts.util import (
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG

# Protects the server from unbounded reads: 3000 steps at the 5-minute
# cadence is ~10 days per request.
MAX_TIME_STEPS = 3000
# Timesteps per read batch (memory bound: 200 x 600 x 600 float64 < 600 MB
# even for a whole-domain polygon).
BATCH = 200

def _decode_fill_value(attrs):
    """The stores carry _FillValue either as a number or as base64-encoded
    little-endian float64 bytes (zarr v3 binary attribute encoding)."""
    fv = attrs.get('_FillValue', attrs.get('missing_value'))
    if fv is None:
        return None
    if isinstance(fv, (int, float)):
        return float(fv)
    if isinstance(fv, str):
        try:
            raw = base64.b64decode(fv)
            if len(raw) == 8:
                return struct.unpack('<d', raw)[0]
            if len(raw) == 4:
                return struct.unpack('<f', raw)[0]
        except Exception:
            return None
    return None

def get_region_vid_json(params):
    """Aggregate a vertically-integrated parameter over a user polygon.

    Region analytics primitive (BirdCast-dashboard analog): for every
    timestep in [startTime, endTime], the mean and max of the parameter
    over the polygon and the estimated number of individuals aloft above
    the polygon (sum of cell value x cell area; valid for areal densities
    such as vid [#/km2]).

    Implementation note: the vid store is chunked (1, 1, 50, 50) --
    ~19 million chunks per variable -- which makes xarray/dask graphs
    explode in memory. The store is therefore read directly with zarr,
    slicing only the polygon's bounding-box window in time batches.

    Payload: radarID, startTime, endTime (Kigali local, converted
    upstream), species ('bird'|'insect'), parameter (default 'vid'),
    polygon = [[lon, lat], ...] with at least 3 vertices.
    """
    for key in ('radarID', 'startTime', 'endTime', 'polygon'):
        if key not in params:
            return response_download_error(
                    f'No parameter <{key}> found.', 'region_vid', 422
                )
    parameter = params.get('parameter', 'vid')
    species_name = params.get('species', 'bird')
    species_value = 1 if species_name == 'bird' else 0

    try:
        poly = np.asarray(
            [[float(p[0]), float(p[1])] for p in params['polygon']],
            dtype=float
        )
        assert poly.ndim == 2 and poly.shape[0] >= 3 and poly.shape[1] == 2
    except Exception:
        msg = 'Invalid parameter <polygon>: expected [[lon, lat], ...] with >= 3 vertices.'
        return response_download_error(msg, 'region_vid', 422)

    zarr_info = GLOBAL_CONFIG['vertical']['zarr']
    zarr_dirfile = zarr_info['file'] % (int(params['radarID']))
    zarr_path = os.path.join(zarr_info['dir'], zarr_dirfile)
    if not os.path.exists(zarr_path):
        return response_download_error(
                'Zarr data not found.', 'region_vid', 422
            )

    store = zarr.open_group(zarr_path, mode='r')
    if parameter not in store:
        available = sorted(
            k for k in store.array_keys()
            if k not in ('time', 'lat', 'lon', 'species')
        )
        msg = f'Unknown parameter <{parameter}>. Available: {available}.'
        return response_download_error(msg, 'region_vid', 422)

    species_axis = store['species'][:]
    sp_idx = np.where(species_axis == species_value)[0]
    if sp_idx.size == 0:
        return response_download_error(
                f'Species <{species_name}> not present in the store.',
                'region_vid', 422
            )
    isp = int(sp_idx[0])

    # time stored as epoch seconds (data_grid_time_encoding)
    time_s = store['time'][:].astype('int64')
    frmt = '%Y-%m-%d %H:%M:%S'
    # request times are already UTC (convert_kigali_utc upstream); anchor
    # them explicitly, otherwise .timestamp() assumes the server timezone
    def _utc_s(t):
        return int(
            datetime.strptime(t, frmt).replace(tzinfo=timezone.utc).timestamp()
        )
    t0 = _utc_s(params['startTime'])
    t1 = _utc_s(params['endTime'])
    it = np.where((time_s >= t0) & (time_s <= t1))[0]
    if it.size == 0:
        return response_download_error(
                'No data in the requested period.', 'region_vid', 422
            )
    if it.size > MAX_TIME_STEPS:
        msg = (f'Requested period spans {int(it.size)} timesteps; '
               f'maximum is {MAX_TIME_STEPS}. Shorten the period.')
        return response_download_error(msg, 'region_vid', 422)
    it0, it1 = int(it[0]), int(it[-1]) + 1

    lon = store['lon'][:]
    lat = store['lat'][:]
    # bounding-box window: only the chunks the polygon can touch are read
    lon_min, lat_min = poly.min(axis=0)
    lon_max, lat_max = poly.max(axis=0)
    ix = np.where((lon >= lon_min) & (lon <= lon_max))[0]
    iy = np.where((lat >= lat_min) & (lat <= lat_max))[0]
    if ix.size == 0 or iy.size == 0:
        msg = 'The polygon contains no grid cells inside the radar coverage.'
        return response_download_error(msg, 'region_vid', 422)
    ix0, ix1 = int(ix[0]), int(ix[-1]) + 1
    iy0, iy1 = int(iy[0]), int(iy[-1]) + 1

    wlon = lon[ix0:ix1]
    wlat = lat[iy0:iy1]
    glon, glat = np.meshgrid(wlon, wlat)
    inside = Path(poly).contains_points(
        np.column_stack([glon.ravel(), glat.ravel()])
    ).reshape(glat.shape)
    if not inside.any():
        msg = 'The polygon contains no grid cells inside the radar coverage.'
        return response_download_error(msg, 'region_vid', 422)
    n_cells = int(inside.sum())

    # equirectangular cell areas (km2); latitude-dependent lon spacing
    dlat = float(abs(lat[1] - lat[0]))
    dlon = float(abs(lon[1] - lon[0]))
    cell_km2 = (dlat * 110.574) * (dlon * 111.32 * np.cos(np.deg2rad(glat)))
    area_km2 = float(cell_km2[inside].sum())

    arr = store[parameter]
    fill = _decode_fill_value(dict(arr.attrs))
    mean_out = np.full(it1 - it0, np.nan)
    max_out = np.full(it1 - it0, np.nan)
    aloft_out = np.full(it1 - it0, np.nan)
    valid_out = np.zeros(it1 - it0, dtype=int)
    outside = ~inside
    for b0 in range(it0, it1, BATCH):
        b1 = min(b0 + BATCH, it1)
        block = np.asarray(
            arr[isp, b0:b1, iy0:iy1, ix0:ix1], dtype='float64'
        )
        if fill is not None:
            block[block == fill] = np.nan
        block[:, outside] = np.nan
        j0, j1 = b0 - it0, b1 - it0
        valid = np.isfinite(block)
        valid_out[j0:j1] = valid.sum(axis=(1, 2))
        has = valid_out[j0:j1] > 0
        with np.errstate(invalid='ignore'):
            mean_out[j0:j1][has] = np.nanmean(
                block[has], axis=(1, 2)
            )
            max_out[j0:j1][has] = np.nanmax(
                block[has], axis=(1, 2)
            )
        aloft = np.nansum(block * cell_km2[None, :, :], axis=(1, 2))
        aloft[~has] = np.nan
        aloft_out[j0:j1] = aloft

    times = [
        datetime.fromtimestamp(int(s), tz=timezone.utc).strftime(frmt)
        for s in time_s[it0:it1]
    ]

    def _round(a, nd=4):
        return [None if not np.isfinite(v) else round(float(v), nd) for v in a]

    attrs = dict(arr.attrs)
    data = {
        'times': times,
        'mean': _round(mean_out),
        'max': _round(max_out),
        'aloft': _round(aloft_out, 1),
        'valid_cells': [int(v) for v in valid_out],
        'n_cells': n_cells,
        'area_km2': round(area_km2, 1),
        'species': species_name,
        'parameter': parameter,
        'name': str(attrs.get('long_name', parameter)),
        'units': str(attrs.get('units', '')),
    }
    return response_download_json(data, 'region_vid')
