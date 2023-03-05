import json
import os
import sys

import psutil
import requests

modelName = 'Lazy English Cards'
deckName = 'Lazy English'


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


def getModel(modelName=modelName):
    """Create params for createModel function"""
    folder = 'assets/'
    os.chdir(folder)
    with open('styling.css', 'r') as file:
        css = file.read()
    with open('back.html', 'r') as file:
        backHtml = file.read()
    with open('front.html', 'r') as file:
        frontHtml = file.read()
    os.chdir('..')
    return {
        'modelName': modelName,
        'inOrderFields': ['Word', 'Sound', 'Meaning', 'IPA'],
        'isCloze': False,
        'css': css,
        'cardTemplates': [{
            'Name': modelName,
            'Front': frontHtml,
            'Back': backHtml
        }]
    }


    
os.chdir('.')

openAnki()

if modelName not in invoke('modelNames'):
    invoke('createModel', **getModel(modelName=modelName))
if deckName not in invoke('deckNames'):
    invoke('createDeck', deck=deckName)