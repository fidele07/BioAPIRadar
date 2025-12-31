import numpy as np
from geopy.distance import geodesic
from .interp import (
        get_line_equation,
        nearest_neighbor_max_radius
    )

def compute_vcross_polar(params, data, lon, lat, alt):
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

    dist = [0]
    for i in range(1, nx):
        p1 = (yl[i - 1], xl[i - 1])
        p2 = (yl[i], xl[i])
        dist.append(dist[-1] + geodesic(p1, p2).km)
    dist = np.array(dist)
    dist = np.round(dist, 4)

    vcross = np.round(vcross, 4)
    vcross = np.where(np.isnan(vcross), None, vcross)

    return {
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

def compute_vcross_grid(params, data, lon, lat, hgt):
    mn_lo, mx_lo = np.min(lon), np.max(lon)
    mn_la, mx_la = np.min(lat), np.max(lat)

    xlon = np.arange(mn_lo, mx_lo, 0.0045)
    xlat = np.arange(mn_la, mx_la, 0.0045)
    xl, yl = get_line_equation(
          xlon, xlat, params['startLon'],
          params['startLat'], params['endLon'],
          params['endLat'], params['segment']
        )

    res_x = np.max(np.diff(lon[:, :2]))
    res_y = np.max(np.diff(lat[:2, :].T))
    max_radius = np.sqrt(res_x**2 + res_y**2)
    points = np.array([lon.ravel(), lat.ravel()]).T
    new_points = np.vstack((xl, yl)).T

    vcross = np.full((len(hgt), len(xl)), np.nan)
    for k in range(len(hgt)):
        tmp = data[k, :, :].ravel()
        im = ~np.isnan(tmp)
        vcross[k, :] = nearest_neighbor_max_radius(
                points[im, :], tmp[im], new_points, max_radius
            )

    dist = [0]
    for i in range(1, len(xl)):
        p1 = (yl[i - 1], xl[i - 1])
        p2 = (yl[i], xl[i])
        dist.append(dist[-1] + geodesic(p1, p2).km)
    dist = np.array(dist)
    dist = np.round(dist, 4)

    vcross = np.round(vcross, 4)
    vcross = np.where(np.isnan(vcross), None, vcross)

    return {
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
