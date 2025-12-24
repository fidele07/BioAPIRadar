
def checkParamBoolean(params, key, default=None):
    ret_error = {'status': -1, 'message': None}
    if not key in params:
        if default is not None:
            params[key] = default
            return {'status': 0, 'params': params}
        else:
            ret_error['message'] = f'No parameter <{key}> found.'
            return ret_error
    else:
        ret_error['message'] = f'Invalid parameter <{key}: {params[key]}>.'
        try:
            if isinstance(params[key], str):
                b = params[key].title()
                b = b[0:4] if b[0] == 'T' else b[0:5]
                try:
                    params[key] = eval(b)
                    return {'status': 0, 'params': params}
                except Exception:
                    return ret_error
            else:
                if not isinstance(params[key], bool):
                    return ret_error
                else:
                    return {'status': 0, 'params': params}
        except Exception:
            return ret_error

def checkParamInteger(params, key, default=None):
    ret_error = {'status': -1, 'message': None}
    if not key in params:
        if default is not None:
            params[key] = default
            return {'status': 0, 'params': params}
        else:
            ret_error['message'] = f'No parameter <{key}> found.'
            return ret_error
    else:
        ret_error['message'] = f'Invalid parameter <{key}: {params[key]}>.'
        try:
            if isinstance(params[key], str):
                params[key] = int(params[key])
                return {'status': 0, 'params': params}
            else:
                if not isinstance(params[key], int):
                    return ret_error
                else:
                    return {'status': 0, 'params': params}
        except Exception:
            return ret_error

def checkParamFloat(params, key):
    ret_error = {'status': -1, 'message': None}
    if not key in params:
        ret_error['message'] = f'No parameter <{key}> found.'
        return ret_error
    else:
        try:
            params[key] = float(params[key])
            return {'status': 0, 'params': params}
        except Exception:
            ret_error['message'] = f'Invalid parameter <{key}: {value}>.'
            return ret_error

def checkParamFloatList(params, key):
    ret_error = {'status': -1, 'message': None}
    if not key in params:
        ret_error['message'] = f'No parameter <{key}> found.'
        return ret_error
    else:
        try:
            params[key] = [float(p) for p in params[key]]
            return {'status': 0, 'params': params}
        except Exception:
            ret_error['message'] = f'Invalid parameter <{key}: {value}>.'
            return ret_error
