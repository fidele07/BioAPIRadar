import os
import netCDF4 as nc
import numpy as np
from geopy.distance import geodesic
from .bioclass import get_class_info
from app.scripts.util import (
        get_data_file_path,
        cftime2datetime,
        response_download_json,
        response_download_error
    )
from app.scripts._global import GLOBAL_CONFIG
from app.scripts.interp import (
        get_line_equation,
        nearest_neighbor_max_radius
    )
import pyart

def get_vcross_bioclass(params):
    class_info = GLOBAL_CONFIG['class']
    file_path = get_data_file_path(class_info, params['time'])
    if file_path is None:
        msg = 'No data found.'
        return response_download_error(
                msg, 'grid_cartesian', 422
            )

    grid = pyart.io.read_grid(file_path)
    param_info = get_class_info(params['class'])
    data = grid.fields[param_info['field']]['data']

    hgt = grid.z['data'].filled(np.nan)
    lon, lat = grid.get_point_longitude_latitude()
    xl, yl = get_line_equation(
          lon[0, :], lat[:, 0], params['startLon'],
          params['startLat'], params['endLon'],
          params['endLat'], params['segment']
        )

    max_radius = np.sqrt(
            np.diff(lon[0, :2])**2 + np.diff(lat[:2, 0])**2
        )
    points = np.array([lon.ravel(), lat.ravel()]).T
    new_points = np.vstack((xl, yl)).T

    vcross = np.full((len(hgt), len(xl)), np.nan)
    for k in range(len(hgt)):
        tmp = data[k, :, :].ravel()
        im = ~tmp.mask
        vcross[k, :] = nearest_neighbor_max_radius(
                points[im, :], tmp[im].data, new_points, max_radius
            )

    time = nc.num2date(
                grid.time['data'][-1],
                units=grid.time['units'],
                calendar=grid.time['calendar']
            )
    time = cftime2datetime(time)
    time = time.strftime('%Y-%m-%d %H:%M:%S')

    dist = [0]
    for i in range(1, len(xl)):
        p1 = (yl[i - 1], xl[i - 1])
        p2 = (yl[i], xl[i])
        dist.append(dist[-1] + geodesic(p1, p2).km)
    dist = np.array(dist)
    dist = np.round(dist, 4)

    class_0 = vcross <= 0.5
    class_1 = vcross > 0.5 
    vcross[class_0] = 0
    vcross[class_1] = 1
    vcross = np.where(np.isnan(vcross), None, vcross)

    out = {
        'vcross': vcross.tolist(), 
        'xaxis': {
                'values': dist.tolist(),
                'label': 'Distance along transect (km)'
            },
        'yaxis': {
                'values': hgt.tolist(),
                'label': 'Height (m)'
            },
        'start_point': {
                'lon': round(xl[0], 4),
                'lat': round(yl[0], 4)
            },
        'end_point':{
                'lon': round(xl[-1], 4),
                'lat': round(yl[-1], 4)
            }
    }

    out['info'] = {
                    'time': time,
                    'name': param_info['name'],
                    'class': params['class']
                }

    return response_download_json(out, 'vertical_cross_sec_bio')
