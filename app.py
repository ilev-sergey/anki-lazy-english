"""
This module allows you to create anki cards with
pronunciation, explanation and examples of the use of English words

The module also provides functions for easier interaction with AnkiConnect:
 invoke, get_model, get_note, get_notes
"""
import functools
import itertools
import json
import logging
import os
import sys
from multiprocessing.dummy import Pool as ThreadPool
from pathlib import Path

import psutil
import requests

from constants import *


def request(action, **params):
    """Form dict of given args to pass to AnkiConnect API"""
    return {"action": action, "params": params, "version": 6}


def invoke(action, **params):
    """Invoke one of available actions with given params

    https://github.com/FooSoft/anki-connect#supported-actions
    """
    request_json = json.dumps(request(action, **params))
    response = requests.post("http://localhost:8765", request_json, timeout=30).json()
    if len(response) != 2:
        raise requests.exceptions.RequestException(
            "response has an unexpected number of fields"
        )
    if "error" not in response:
        raise requests.exceptions.RequestException(
            "response is missing required error field"
        )
    if "result" not in response:
        raise requests.exceptions.RequestException(
            "response is missing required result field"
        )
    if response["error"] is not None:
        raise requests.exceptions.RequestException(response["error"])
    return response["result"]


def open_anki():
    """Open Anki if not opened"""
    if "anki.exe" not in (p.name() for p in psutil.process_iter()):
        if "win" in sys.platform:
            os.startfile("C:\\Program Files\\Anki\\anki.exe")


def get_model(model_name, links={}):
    """Create params for createModel action"""
    folder = "assets/"
    os.chdir(folder)
    with open("styling.css", "r", encoding="utf-8") as file:
        css = file.read()
    with open("back.html", "r", encoding="utf-8") as file:
        back_html = file.read()
    with open("front.html", "r", encoding="utf-8") as file:
        front_html = file.read()
    os.chdir("..")
    back_html += "<p>"
    dicts = DICTIONARIES
    dicts |= links
    for key, value in dicts.items():
        if value:
            match key:
                case "Oxford":
                    back_html += '<a href="https://www.oxfordlearnersdictionaries.com/definition/english/{{Word}}"><img src="https://fontslogo.com/wp-content/uploads/2017/10/Oxford-Dictionaries-Logo-Font.jpg"></a>\n'
                case "Cambridge":
                    back_html += '<a href="https://dictionary.cambridge.org/dictionary/english/{{Word}}/"><img src="https://w7.pngwing.com/pngs/647/218/png-transparent-coat-of-arms-of-the-university-of-cambridge-university-of-oxford-ulverston-victoria-high-school-others-text-logo-symmetry.png"></a>\n'
                case "Macmillan":
                    back_html += '<a href="https://www.macmillandictionary.com/dictionary/british/{{Word}}"><img src="https://pbs.twimg.com/profile_images/1225002102608494592/GRFg82nJ_400x400.jpg"></a>\n'
                case "Urban Dictionary":
                    back_html += '<a href="https://www.urbandictionary.com/define.php?term={{Word}}"><img src="https://play-lh.googleusercontent.com/unQjigibyJQvru9rcCOX7UCqyByuf5-h_tLpA-9fYH93uqrRAnZ0J2IummiejMMhi5Ch"></a>\n'
                case "Cambridge (ru)":
                    back_html += 'ru:<a href="https://dictionary.cambridge.org/dictionary/english-russian/{{Word}}/"><img src="https://w7.pngwing.com/pngs/647/218/png-transparent-coat-of-arms-of-the-university-of-cambridge-university-of-oxford-ulverston-victoria-high-school-others-text-logo-symmetry.png"></a></p>\n'
    back_html += "</p>"
    return {
        "modelName": model_name,
        "inOrderFields": ["Word", "Sound", "Meaning", "IPA"],
        "isCloze": False,
        "css": css,
        "cardTemplates": [{"Name": model_name, "Front": front_html, "Back": back_html}],
    }


def parse_json(word):
    """Parse Json received from Free Dictionary API"""
    logging.info("parsing: %s", word)
    word_json = requests.get(
        f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=10
    ).json()[0]
    res = ""
    for elem in word_json["meanings"]:
        part_of_speech = elem["partOfSpeech"]
        meanings = elem["definitions"]
        str_meaning = f"{part_of_speech}:"
        for i, meaning in enumerate(meanings, 1):
            definition = meaning["definition"]
            str_definition = f"<div>{i}) {definition}<br /> "
            if meaning.get("example"):
                str_definition += "&nbsp;→ " + meaning.get("example") + "<br />"
            if meaning.get("synonyms"):
                str_definition += (
                    "&nbsp; synonyms: " + ", ".join(meaning.get("synonyms")) + "<br/>"
                )
            if meaning.get("antonyms"):
                str_definition += (
                    "&nbsp; antonyms: " + ", ".join(meaning.get("antonyms")) + "<br/>"
                )
            str_meaning += f"{str_definition}</div>"
        if elem.get("synonyms"):
            str_meaning += "synonyms: " + ", ".join(elem.get("synonyms")) + "<br />"
        res += str_meaning + "<hr /> "
    audio = ""
    for phonetic in word_json["phonetics"]:
        if phonetic["audio"]:
            audio = phonetic["audio"]
            break
    return {
        "fields": {
            "Word": word_json["word"],
            "IPA": word_json.get("phonetic", ""),
            "Meaning": res[:-1],
        },
        "audio": [{"url": audio, "filename": audio, "fields": ["Sound"]}]
        if audio
        else None,
    }


def get_note(
    word, cache, deck_name=DECK_NAME, model_name=MODEL_NAME, allow_duplicate=False
):
    """Create params for addNote action"""
    if CACHE_ENABLED:
        if word in cache:
            return cache[word]
    word_json = parse_json(word)
    note = {
        "deckName": deck_name,
        "modelName": model_name,
        "options": {
            "allowDuplicate": allow_duplicate,
        },
        "fields": word_json["fields"],
        "audio": word_json["audio"],
    }
    if CACHE_ENABLED:
        cache[word] = note
    return note


def threading(func):
    """Decorator for threading"""

    @functools.wraps(func)
    def wrapper(iterable, **kwargs):
        map_func = functools.partial(func, **kwargs)
        with ThreadPool() as pool:
            results = pool.map(map_func, split_iterable(iterable))
        return list(itertools.chain.from_iterable(results))

    return wrapper


@threading
def get_notes(words, **kargs):
    """Create params for addNotes action"""
    return [get_note(word, **kargs) for word in words]


def get_words(filename):
    """Get words from file"""
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    if not os.path.exists(filename):
        open(filename, "a", encoding="utf-8").close()
    with open(filename, "r", encoding="utf-8") as file:
        words = file.read().splitlines()
    return words


def load_cache():
    """Get cache from json file"""
    Path(CACHE_PATH).parent.mkdir(parents=True, exist_ok=True)
    if os.path.exists(CACHE_PATH):
        if os.path.getsize(CACHE_PATH) > 0:
            with open(CACHE_PATH, "r", encoding="utf-8") as file:
                return json.load(file)
        return {}
    open(CACHE_PATH, "a", encoding="utf-8").close()
    return {}


def split_iterable(iterable, size=5):
    """Split iterable into iterables"""
    if sys.version_info >= (3, 12):
        for batch in itertools.batched(iterable, size):
            yield batch
    else:
        for i in range(0, len(iterable), size):
            yield iterable[i : i + size]


def main():
    """Create model and deck, add cards to deck

    Create model with name MODEL_NAME if not exists
    Create deck with name DECK_NAME if not exists
    Add card to deck for each uncached word from WORDLIST_NAME
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    os.chdir(".")

    open_anki()

    if MODEL_NAME not in invoke("modelNames"):
        invoke("createModel", **get_model(model_name=MODEL_NAME))
    if DECK_NAME not in invoke("deckNames"):
        invoke("createDeck", deck=DECK_NAME)
    cache = load_cache() if CACHE_ENABLED else {}

    words = get_words(WORDLIST_NAME)
    invoke("addNotes", notes=get_notes(words, cache=cache))

    if CACHE_ENABLED:
        with open(CACHE_PATH, "w", encoding="utf-8") as file:
            json.dump(cache, file, indent=2)


if __name__ == "__main__":
    main()
