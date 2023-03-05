import json
import logging
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


def parseJson(word):
    """Parse Json received from Free Dictionary API"""
    logging.info(f'parsing: {word}')
    wordJson = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}').json()[0]
    res = ''
    for elem in wordJson['meanings']:
        partOfSpeech = elem['partOfSpeech']
        meanings = elem['definitions']
        strMeaning = f'{partOfSpeech}:'
        for i, meaning in enumerate(meanings, 1):
            definition = meaning['definition']
            strDefinition = f'<div>{i}) {definition}<br /> '
            if meaning.get('example'):
                strDefinition += '&nbsp;→ ' + meaning.get('example') + '<br />'
            if meaning.get('synonyms'):
                strDefinition += '&nbsp; synonyms: ' + ', '.join(meaning.get('synonyms')) + '<br />'
            if meaning.get('antonyms'):
                strDefinition += '&nbsp; antonyms: ' + ', '.join(meaning.get('antonyms')) + '<br />'
            strMeaning += f'{strDefinition}</div>'
        if elem.get('synonyms'):
            strMeaning += 'synonyms: ' + ', '.join(elem.get('synonyms')) + '<br />'
        res += strMeaning + '<hr /> '
    audio = ''
    for phonetic in wordJson['phonetics']:
        if phonetic['audio']:
            audio = phonetic['audio']
            break
    return {
        'fields': {
            'Word': wordJson['word'],
            'IPA': wordJson.get('phonetic', ''),
            'Meaning': res[:-1],
        },
        'audio': [{
            'url': audio,
            'filename': audio,
            'fields': [
                'Sound'
            ]
        }] if audio else None
    }


    
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
os.chdir('.')

openAnki()

if modelName not in invoke('modelNames'):
    invoke('createModel', **getModel(modelName=modelName))
if deckName not in invoke('deckNames'):
    invoke('createDeck', deck=deckName)