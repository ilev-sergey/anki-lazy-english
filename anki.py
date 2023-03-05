import json
import os
import sys

import psutil
import requests


def request(action, **params):
    return {"action": action, "params": params, "version": 6}


def invoke(action, **params):
    requestJson = json.dumps(request(action, **params))
    response = requests.post('http://localhost:8765', requestJson).json()
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']


def openAnki():
    """Open Anki if not opened"""
    if 'anki.exe' not in (p.name() for p in psutil.process_iter()):
        if 'win' in sys.platform:
            os.startfile('C:\\Program Files\\Anki\\anki.exe')


openAnki()