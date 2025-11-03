import yaml
import io
import os
import sys
import json
import glob
import numpy as np
import contextlib
from datetime import datetime
from flask import (
            make_response,
            jsonify,
            request
        )

def load_yaml_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            conf = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f'Error {e}')

    return conf

def format_get_request(args):
    params = args.to_dict(flat = False)
    pr = dict()
    for key, value in params.items():
        pr[key] = value if len(value) > 1 else value[0]

    return pr

def read_binary_file(filename):
    with open(filename, 'rb') as b:
        buf = io.BytesIO(b.read())

    return buf

def response_download_file(data, filename, mimetype):
    response = make_response(
            jsonify({'status': 0, 'data': data}),
            200
         )
    response.mimetype = mimetype
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

def response_download_error(message, filename, code=422):
    response = make_response(
            jsonify({'message': message, 'status': -1}),
            code
         )
    response.mimetype = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}.json'
    return response

def response_download_json(data, params, filename):
    filename = f'{filename}.json'
    mimetype = 'application/json'

    if params['httpMethod'] == 'POST':
        return json.dumps(
                {'status': 0, 'data': data,
                 'filename': filename,
                 'mimetype': mimetype}
            )
    else:
        return response_download_file(
                data, filename, mimetype
            )

def post_get_request():
    if request.method == 'GET':
        params = format_get_request(request.args)
    else:
        params = request.get_json()
    return params

def response_download_data(callback):
    params = post_get_request()

    # check_user = checkUserDataAPIKey(params, request)
    # if check_user['status'] == -1:
    #     if request.method == 'GET':
    #         return make_response(
    #                 jsonify({'message': check_user['message']}),
    #                 check_user['code']
    #             )
    #     else:
    #         return json.dumps(check_user)

    # check_params = checkParamsRequest(params)
    # if check_params['status'] == -1:
    #     if request.method == 'GET':
    #         return make_response(
    #                 jsonify({'message': check_params['message']}),
    #                 400
    #             )
    #     else:
    #         check_params['code'] = 400
    #         return json.dumps(check_params)

    try:
        # params = check_params['params']
        # params['user'] = check_user['user']
        params['httpMethod'] = request.method
        return callback(params)
    except Exception as e:
        if request.method == 'GET':
            return make_response(
                    jsonify({'message': str(e)}),
                    500
                )
        else:
            return json.dumps(
                    {'status': -1, 'message': str(e)}
                )

@contextlib.contextmanager
def suppress_stdout():
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

def cftime2datetime(time):
    return datetime(
                    time.year,
                    time.month,
                    time.day,
                    time.hour,
                    time.minute,
                    time.second
                    )

def npdt64todatetime(time):
    time = pd.Timestamp(time)
    return datetime(
                    time.year,
                    time.month,
                    time.day,
                    time.hour,
                    time.minute,
                    time.second
                    )

def pretty(low, high, n):
    range = _nicenumber(high - low, False)
    d = _nicenumber(range / (n - 1), True)
    miny = np.floor(low / d) * d
    maxy = np.ceil(high / d) * d

    return np.arange(miny, maxy + 0.5 * d, d)

def _nicenumber(x, round):
    exp = np.floor(np.log10(x))
    f = x / 10 ** exp

    if round:
        if f < 1.5:
            nf = 1.0
        elif f < 3.0:
            nf = 2.0
        elif f < 7.0:
            nf = 5.0
        else:
            nf = 10.0
    else:
        if f <= 1.0:
            nf = 1.0
        elif f <= 2.0:
            nf = 2.0
        elif f <= 5.0:
            nf = 5.0
        else:
            nf = 10.0

    return nf * 10.0 ** exp

def get_data_dates_dir(data_info):
    dates_dir = data_info['dir']
    dates_dir = [os.path.join(dates_dir, d) for d in os.listdir(dates_dir)]
    if len(dates_dir) == 0:
        return None
    dates_dir = [os.path.basename(d) for d in dates_dir if os.path.isdir(d)]
    if len(dates_dir) == 0:
        return None
    tmp_path = []
    for d in dates_dir:
        try:
            tmp = datetime.strptime(d, data_info['format_dir'])
            tmp_path += [d]
        except:
            continue
    if len(tmp_path) == 0:
        return None

    return tmp_path

def get_data_file_path(data_info, time_str):
    format_time = '%Y-%m-%d %H:%M:%S'
    time_req = datetime.strptime(time_str, format_time)
    date_dir = time_req.strftime(data_info['format_dir'])
    data_dir = os.path.join(data_info['dir'], date_dir)
    if not os.path.isdir(data_dir):
        return None
    data_files = glob.glob(f'{data_dir}/{data_info['pattern']}')
    data_files = [os.path.basename(p) for p in data_files]
    date_files = [datetime.strptime(f, data_info['format_file']) for f in data_files]
    date = min(date_files, key=lambda dt: abs(dt - time_req))
    file = date.strftime(data_info['format_file'])
    return os.path.join(data_dir, file)

def get_data_files_list(data_info, start_time, end_time):
    format_time = '%Y-%m-%d %H:%M:%S'
    start = datetime.strptime(start_time, format_time)
    end = datetime.strptime(end_time, format_time)
    start_date = start.date()
    end_date = end.date()

    dates_dir = get_data_dates_dir(data_info)
    if dates_dir is None:
        return None
    dt_dir = [datetime.strptime(d, data_info['format_dir']) for d in dates_dir]
    dt_dir = [d.date() for d in  dt_dir]
    it = [d >= start_date and d <= end_date for d in dt_dir]
    if not any(it):
        return None
    dates_dir = [dates_dir[i] for i, j in enumerate(it) if j]

    list_out = []
    for d in dates_dir:
        data_dir = os.path.join(data_info['dir'], d)
        data_files = glob.glob(f'{data_dir}/{data_info['pattern']}')
        if len(data_files) == 0:
            continue
        data_files = [os.path.basename(p) for p in data_files]
        date_files = [datetime.strptime(f, data_info['format_file']) for f in data_files]
        it = [t >= start and t <= end for t in date_files]
        if not any(it):
            continue
        data_files = [data_files[i] for i, j in enumerate(it) if j]
        list_out += [{'dir': d, 'files': data_files}]
    if len(list_out) == 0:
        return None

    return list_out
