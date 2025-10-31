import netCDF4 as nc
import numpy as np
from .util import cftime2datetime

def read_netcdf_nc(nc_path, varid, ncinfo):
    ncdata = nc.Dataset(nc_path)
    vardata = ncdata.variables[varid]

    data = vardata[:]
    mask = np.ma.getmask(data)
    if len(mask.shape) == 0:
        mask = np.zeros(np.prod(data.shape), dtype=bool)
        mask = mask.reshape(data.shape)
        data = np.ma.masked_array(data, mask=mask)
        data.fill_value = ncinfo['missval']

    lon = ncdata.variables[ncinfo['lon']][:]
    lat = ncdata.variables[ncinfo['lat']][:]
    time = None

    var_names = list(ncdata.variables.keys())
    if ncinfo['time'] in var_names:
        timeinfo = ncdata.variables[ncinfo['time']]
        units = timeinfo.units
        calendar = 'standard'
        if hasattr(timeinfo, 'calendar'):
            calendar = timeinfo.calendar
        time = nc.num2date(
                    timeinfo[:],
                    units=units,
                    calendar=calendar
                )
        time = cftime2datetime(time.filled()[0])

    name = vardata.long_name
    units = vardata.units
    ncdata.close()
    return {
             'lon': lon, 'lat': lat,
             'time': time, 'data': data,
             'name': name, 'units': units,
             'parameter': varid
            }
