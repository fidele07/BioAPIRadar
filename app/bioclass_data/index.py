from flask import Blueprint, request
from flask import current_app as app

from app.scripts.util import (
        response_download_data,
        post_get_request
    )
from .scripts.bioclass import download_bioclass
from .scripts.vcross_sec import get_vcross_bioclass

bioclass_data = Blueprint('bioclass_data', __name__)

@bioclass_data.route('/get_bioclass', methods=['GET', 'POST'])
def get_bioclass():
    """
    Biological-Meteorological Classification.
    Bird-Insect Classification.
    """
    return response_download_data(download_bioclass)

@bioclass_data.route('/vcross_section_bioclass', methods=['GET', 'POST'])
def vcross_section_bioclass():
    """
    Vertical cross-section
    Biological-Meteorological Classification.
    Bird-Insect Classification.
    """
    return response_download_data(get_vcross_bioclass)

