from flask import Blueprint
from flask import current_app as app

from app.scripts.util import response_download_data
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
    return response_download_data(download_vp)

@biorad_data.route('/get_vpts', methods=['GET', 'POST'])
def get_vpts():
    """Vertical profiles time series."""
    return response_download_data(download_vpts)

@biorad_data.route('/get_vtip', methods=['GET', 'POST'])
def get_vtip():
    """Vertical and time integration of profiles."""
    return response_download_data(download_vtip)

@biorad_data.route('/get_sevip', methods=['GET', 'POST'])
def get_sevip():
    """Spatial estimates of vertically integrated parameters."""
    return response_download_data(download_sevip)

