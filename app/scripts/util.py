import yaml
import io
import os
import sys
import json
from flask import make_response, jsonify
import contextlib

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

