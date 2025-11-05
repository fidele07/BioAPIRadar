import os
import netCDF4 as nc
import numpy as np
from geopy.distance import geodesic
from .rinfo import get_field_info
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

def vcross_section_polar(params):
    polar_info = GLOBAL_CONFIG['radar']['polar']
    file_path = get_data_file_path(polar_info, params['time'])
    if file_path is None:
        msg = 'No data found.'
        return response_download_error(
                msg, 'polar_volume', 422
            )
    radar = pyart.aux_io.read_odim_h5(
            file_path, file_field_names=True, delay_field_loading=True
        )

    param_info = get_field_info(params['parameter'])
    if params['parameter'] == 'dr':
        zdr = radar.fields['ZDR']['data']
        rho = radar.fields['RHOHV']['data']
        num = 1 + zdr - 2 * (zdr**0.5) * rho
        den = 1 + zdr + 2 * (zdr**0.5) * rho
        data = 10 * np.log10(num / den)
    else:
        data = radar.fields[param_info['field']]['data']

    data = data.filled(np.nan)
    radar_alt = radar.altitude['data']
    sweeps = radar.sweep_number['data']
    lon = []
    lat = []
    alt = []
    for s in sweeps:
        slat, slon, salt = radar.get_gate_lat_lon_alt(s)
        lon += [slon]
        lat += [slat]
        alt += [salt - radar_alt]
    lon = np.vstack(lon)
    lat = np.vstack(lat)
    alt = np.vstack(alt)

    mn_lo, mx_lo = np.min(lon), np.max(lon)
    mn_la, mx_la = np.min(lat), np.max(lat)
    mn_al, mx_al = np.min(alt), np.max(alt)

    hgt = np.linspace(0, 5000, 21)
    xlon = np.arange(mn_lo, mx_lo, 0.0045)
    xlat = np.arange(mn_la, mx_la, 0.0045)
    xl, yl = get_line_equation(
          xlon, xlat, params['startLon'],
          params['startLat'], params['endLon'],
          params['endLat'], params['segment']
        )
    nx = len(xl)
    nz = len(hgt)
    zl1 = np.repeat(hgt, nx)
    xl1 = np.concatenate([xl] * nz)
    yl1 = np.concatenate([yl] * nz)

    # scaling
    s_lo = (lon - mn_lo) / (mx_lo - mn_lo)
    s_la = (lat - mn_la) / (mx_la - mn_la)
    s_al = (alt - mn_al) / (mx_al - mn_al)

    s_xl = (xl1 - mn_lo) / (mx_lo - mn_lo)
    s_yl = (yl1 - mn_la) / (mx_la - mn_la)
    s_zl = (zl1 - mn_al) / (mx_al - mn_al)

    max_radius = np.sqrt(
            np.diff(s_xl[:2])**2 + np.diff(s_yl[:2])**2 + s_zl[nx]**2
        )
    points = np.array([s_lo.ravel(), s_la.ravel(), s_al.ravel()]).T
    new_points = np.vstack((s_xl, s_yl, s_zl)).T

    tmp = data.ravel()
    im = ~np.isnan(tmp)
    vcross = nearest_neighbor_max_radius(
                points[im, :], tmp[im], new_points, 2 * max_radius
            )
    vcross = vcross.reshape((nz, nx))

    time = nc.num2date(
                radar.time['data'][-1],
                units=radar.time['units'],
                calendar=radar.time['calendar']
            )
    time = cftime2datetime(time)
    time = time.strftime('%Y-%m-%d %H:%M:%S')

    dist = [0]
    for i in range(1, nx):
        p1 = (yl[i - 1], xl[i - 1])
        p2 = (yl[i], xl[i])
        dist.append(dist[-1] + geodesic(p1, p2).km)
    dist = np.array(dist)
    dist = np.round(dist, 4)

    vcross = np.round(vcross, 4)
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
                    'units': param_info['units'],
                    'type': params['type']
                }

    return response_download_json(out, 'vertical_cross_sec_polar')
