import yaml
import io
import os
import sys
import json
import numpy as np
import contextlib
from datetime import datetime
from flask import make_response, jsonify

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
    response = make_response(data, 200)
    response.mimetype = mimetype
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

def response_download_error(message, filename, code=422):
    response = make_response(jsonify({'message': message, 'status': -1}), code)
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

