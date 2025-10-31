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
from .scripts.sevip import download_sevip

biorad_data = Blueprint('biorad_data', __name__)

@biorad_data.route('/get_vp', methods=['GET', 'POST'])
def get_vp():
    """Vertical profiles."""
    return _get_vp_data(download_vp)

@biorad_data.route('/get_vpts', methods=['GET', 'POST'])
def get_vpts():
    """Vertical profiles time series."""
    return _get_vp_data(download_vpts)

@biorad_data.route('/get_vtip', methods=['GET', 'POST'])
def get_vtip():
    """Vertical and time integration of profiles"""
    return _get_vp_data(download_vtip)

@biorad_data.route('/get_sevip', methods=['GET', 'POST'])
def get_sevip():
    """Spatial estimates of vertically integrated parameters."""
    return _get_vp_data(download_sevip)

def _get_vp_data(callback):
    if request.method == 'GET':
        params = format_get_request(request.args)
    else:
        params = request.get_json()

    try:
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
