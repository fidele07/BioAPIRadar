from flask import Blueprint, request
from flask import make_response, jsonify
from flask import current_app as app
import json
import os

bioclass_data = Blueprint('bioclass_data', __name__)
