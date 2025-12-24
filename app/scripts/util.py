import yaml
import re
import io
import os
import sys
import json
import glob
import numpy as np
import contextlib
import base64
from datetime import datetime
import pytz
from flask import (
            make_response,
            jsonify,
            request,
            Response
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

def response_download_json(data, filename):
    filename = f'{filename}.json'
    mimetype = 'application/json'
    return response_download_file(
            data, filename, mimetype
        )

def response_download_image(data, filename, ext):
    filename = f'{filename}.{ext}'
    if ext == 'jpg':
        ext = 'jpeg'
    mimetype = f'image/{ext}'
    if request.method == 'POST':
        return response_download_file(
                data, filename, mimetype
            )
    else:
        cd = f'attachment; filename={filename}'
        return Response(
                png_base64_binary(data),
                mimetype=mimetype,
                headers={'Content-Type': mimetype,
                         'Content-Disposition': cd}
            )

def png_base64_binary(png_base64):
    ixc = png_base64.find(',')
    png_data = png_base64[ixc + 1:]
    bin_data = base64.b64decode(png_data)
    return bin_data

def post_get_request():
    if request.method == 'GET':
        params = format_get_request(request.args)
    else:
        params = request.get_json()
    return params

def response_download_data(callback):
    params = post_get_request()
    try:
        # params = check_params['params']
        # params['user'] = check_user['user']
        params = convert_kigali_utc(params)
        return callback(params)
    except Exception as e:
        response = make_response(
                jsonify({'status': -1, 'message': str(e)}),
                500
            )
        response.mimetype = 'application/json'
        return response

def convert_kigali_utc(params):
    if 'time' in params:
        params['time'] = kigali2utc(params['time'])
    if 'startTime' in params:
        params['startTime'] = kigali2utc(params['startTime'])
    if 'endTime' in params:
        params['endTime'] = kigali2utc(params['endTime'])
    return params

@contextlib.contextmanager
def suppress_stdout():
    with open(os.devnull, 'w') as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

def kigali2utc(time):
    frmt = '%Y-%m-%d %H:%M:%S'
    kigali_t = datetime.strptime(time, frmt)
    kigali_tz = pytz.timezone('Africa/Kigali')
    kigali_dt = kigali_tz.localize(kigali_t)
    utc_dt = kigali_dt.astimezone(pytz.utc)
    return utc_dt.strftime(frmt)

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
    data_files = glob.glob(f'{data_dir}/{data_info['pattern1']}')
    if len(data_files) == 0:
        return None
    data_files = [os.path.basename(p) for p in data_files]
    ## old
    # date_files = [datetime.strptime(f, data_info['format_file']) for f in data_files]
    # date = min(date_files, key=lambda dt: abs(dt - time_req))
    # file = date.strftime(data_info['format_file'])
    ## new
    date_files = extract_filename_dates(data_files, data_info['format_file'])
    if len(date_files) == 0:
        return None
    it = [d is None for d in date_files]
    if all(it):
        return None
    data_files = [data_files[i] for i, j in enumerate(it) if not j]
    date_files = [date_files[i] for i, j in enumerate(it) if not j]
    date_files = [datetime.strptime(f, '%Y%m%d%H%M%S') for f in date_files]
    it = min(range(len(date_files)), key=lambda i: abs(date_files[i] - time_req))
    file = data_files[it]
    ##
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
        data_files = glob.glob(f'{data_dir}/{data_info['pattern1']}')
        if len(data_files) == 0:
            continue
        data_files = sorted([os.path.basename(p) for p in data_files])
        ## old 
        # date_files = [datetime.strptime(f, data_info['format_file']) for f in data_files]
        ## new
        date_files = extract_filename_dates(data_files, data_info['format_file'])
        if len(date_files) == 0:
            continue
        it = [d is None for d in date_files]
        if all(it):
            continue
        data_files = [data_files[i] for i, j in enumerate(it) if not j]
        date_files = [date_files[i] for i, j in enumerate(it) if not j]
        date_files = [datetime.strptime(f, '%Y%m%d%H%M%S') for f in date_files]
        ##
        it = [t >= start and t <= end for t in date_files]
        if not any(it):
            continue
        data_files = [data_files[i] for i, j in enumerate(it) if j]
        list_out += [{'dir': d, 'files': data_files}]

    if len(list_out) == 0:
        return None

    return list_out

def double_backslash_non_alnum(s):
    return re.sub(r'([^A-Za-z0-9])', r'\\\1', s)

def double_backslash_non_alnum_list(strings):
    if isinstance(strings, str):
        strings = [strings]
    escaped = []
    for s in strings:
        for v in set(re.findall(r'[^A-Za-z0-9]', s)):
            s = s.replace(v, '\\' + v)
        escaped.append(s)
    return escaped

def extract_filename_dates(filenames, fileformat):
    expr = [m.start() for m in re.finditer('%', fileformat)]
    length_expr = [2] * len(expr)
    ret = []
    if expr:
        rr = [False]
        ss = [1]
        se = [len(fileformat)]
        nl = len(expr)
        for i in range(nl):
            rr += [True, False]
            ss += [expr[i] + 1, expr[i] + length_expr[i] + 1]
            j = nl - i - 1
            se = [expr[j], expr[j] + length_expr[j]] + se

        res = []
        for i in range(len(rr)):
            v = fileformat[ss[i]-1:se[i]]
            if v == '' or rr[i]:
                continue
            res.append(v)

        if res:
            res = list(dict.fromkeys(res))
            # res = [double_backslash_non_alnum(r) for r in res]
            res = double_backslash_non_alnum_list(res)
            pattern = re.sub(r'\\\*', '.+', '|'.join(res))
            for fname in filenames:
                cleaned = re.sub(pattern, '', fname)
                ret.append(cleaned)
    if ret:
        ret = [None if re.search(r'[^0-9]', r) else r for r in ret]
    return ret
