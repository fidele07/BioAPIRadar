from flask import Blueprint, request
from flask import make_response, jsonify
from flask import current_app as app
import json
import os

from app.scripts._global import GLOBAL_CONFIG
from app.scripts.util import format_get_request
from .scripts.vpts import (
                    download_vp,
                    download_vpts,
                    download_vtip
                )

biorad_data = Blueprint('biorad_data', __name__)

@biorad_data.route('/get_vp', methods=['GET', 'POST'])
def get_vp():
    if request.method == 'GET':
        params = format_get_request(request.args)
    else:
        params = request.get_json()

    try:
        params['httpMethod'] = request.method
        return download_vp(params)
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

@biorad_data.route('/get_vpts', methods=['GET', 'POST'])
def get_vpts():
    if request.method == 'GET':
        params = format_get_request(request.args)
    else:
        params = request.get_json()

    try:
        params['httpMethod'] = request.method
        return download_vpts(params)
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

@biorad_data.route('/get_vtip', methods=['GET', 'POST'])
def get_vtip():
    if request.method == 'GET':
        params = format_get_request(request.args)
    else:
        params = request.get_json()

    try:
        params['httpMethod'] = request.method
        return download_vtip(params)
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

###
# @biorad_data.route('/get_test', methods=['GET', 'POST'])
# def get_test():
#     if request.method == 'GET':
#         params = format_get_request(request.args)
#     else:
#         params = request.get_json()

#     check_user = checkUserDataAPIKey(params, request)
#     if check_user['status'] == -1:
#         if request.method == 'GET':
#             return make_response(
#                     jsonify({'message': check_user['message']}),
#                     check_user['code']
#                 )
#         else:
#             return json.dumps(check_user)

#     check_params = checkParamsRequest(params)
#     if check_params['status'] == -1:
#         if request.method == 'GET':
#             return make_response(
#                     jsonify({'message': check_params['message']}),
#                     400
#                 )
#         else:
#             check_params['code'] = 400
#             return json.dumps(check_params)

#     try:
#         params = check_params['params']
#         params['user'] = check_user['user']
#         params['httpMethod'] = request.method
#         return download_test(params)
#     except Exception as e:
#         if request.method == 'GET':
#             return make_response(
#                     jsonify({'message': str(e)}),
#                     500
#                 )
#         else:
#             return json.dumps(
#                     {'status': -1, 'message': str(e)}
#                 )
