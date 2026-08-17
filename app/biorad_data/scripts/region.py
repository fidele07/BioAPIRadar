import os
from datetime import datetime

import numpy as np
import xarray as xr
from matplotlib.path import Path

from app.scripts.util import (
        open_zarr_retry,
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG

# Protects the server from unbounded reads: 3000 steps at the 5-minute
# cadence is ~10 days per request.
MAX_TIME_STEPS = 3000

def get_region_vid_json(params):
    """Aggregate a vertically-integrated parameter over a user polygon.

    Region analytics primitive (BirdCast-dashboard analog): for every
    timestep in [startTime, endTime], the mean and max of the parameter
    over the polygon and the estimated number of individuals aloft above
    the polygon (sum of cell value x cell area; valid for areal densities
    such as vid [#/km2]).

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
    species = 1 if species_name == 'bird' else 0

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

    ds = open_zarr_retry(zarr_path)
    if parameter not in ds:
        msg = f'Unknown parameter <{parameter}>. Available: {sorted(ds.data_vars)}.'
        return response_download_error(msg, 'region_vid', 422)

    frmt = '%Y-%m-%d %H:%M:%S'
    t0 = np.datetime64(datetime.strptime(params['startTime'], frmt))
    t1 = np.datetime64(datetime.strptime(params['endTime'], frmt))
    ds = ds.sel(species=species)
    ds = ds.sel(time=slice(t0, t1))
    if ds.time.size == 0:
        return response_download_error(
                'No data in the requested period.', 'region_vid', 422
            )
    if ds.time.size > MAX_TIME_STEPS:
        msg = (f'Requested period spans {int(ds.time.size)} timesteps; '
               f'maximum is {MAX_TIME_STEPS}. Shorten the period.')
        return response_download_error(msg, 'region_vid', 422)

    lon = ds.lon.values
    lat = ds.lat.values
    grid_lon, grid_lat = np.meshgrid(lon, lat)
    inside = Path(poly).contains_points(
        np.column_stack([grid_lon.ravel(), grid_lat.ravel()])
    ).reshape(grid_lat.shape)
    if not inside.any():
        msg = 'The polygon contains no grid cells inside the radar coverage.'
        return response_download_error(msg, 'region_vid', 422)

    # equirectangular cell areas (km2); latitude-dependent lon spacing
    dlat = float(abs(lat[1] - lat[0]))
    dlon = float(abs(lon[1] - lon[0]))
    cell_km2 = (dlat * 110.574) * (dlon * 111.320 * np.cos(np.deg2rad(grid_lat)))

    mask = xr.DataArray(inside, dims=('lat', 'lon'))
    areas = xr.DataArray(cell_km2, dims=('lat', 'lon'))
    var = ds[parameter]

    # dask-lazy reductions: the store is chunked time=1, so this streams
    # one timestep at a time instead of materializing (time, 600, 600).
    region = var.where(mask)
    mean_series = region.mean(dim=('lat', 'lon'), skipna=True).compute()
    max_series = region.max(dim=('lat', 'lon'), skipna=True).compute()
    # individuals aloft above the polygon: NaN cells contribute 0
    aloft_series = (region * areas).sum(
        dim=('lat', 'lon'), skipna=True
    ).compute()
    valid_series = region.notnull().sum(dim=('lat', 'lon')).compute()

    times = ds.time.values.astype('datetime64[s]').astype(datetime)
    n_cells = int(inside.sum())

    def _round(a, nd=4):
        return [None if not np.isfinite(v) else round(float(v), nd) for v in a]

    data = {
        'times': [t.strftime(frmt) for t in times],
        'mean': _round(mean_series.values),
        'max': _round(max_series.values),
        'aloft': _round(aloft_series.values, 1),
        'valid_cells': [int(v) for v in valid_series.values],
        'n_cells': n_cells,
        'area_km2': round(float(cell_km2[inside].sum()), 1),
        'species': species_name,
        'parameter': parameter,
        'name': str(var.attrs.get('long_name', parameter)),
        'units': str(var.attrs.get('units', '')),
    }
    return response_download_json(data, 'region_vid')
