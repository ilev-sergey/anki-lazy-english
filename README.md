# Lazy English Cards

This is an application for [Anki] that makes it easy to add cards with English words, their pronunciation, explanation and usage examples. All you need is a wordlist.

This app uses [AnkiConnect] to add notes to Anki and [Free Dictionary API] to get info about required word.

## How to install

```
pip install -r requirements.txt
```

## How to use

### Upload wordlist from file

- Create a `words.txt` file in the app folder
- Add your wordlist to the file (write one word per line)
- Run `app.py`

For further use, you can overwrite existing words with new ones, or add new words anywhere in the file. The script doesn't modify this file in any way, so you can keep your wordlist this way if you want.

### Upload the wordlist interactively

- Run `gui.py`
- Paste your wordlist into the input field (write one word per line)
- Press the `Submit` button
- Wait until `cards created` message is displayed
- Close the application

## To do

- make add-on from script (see also [#1])
- add tests

## Features
- plugin supports multutreading to add notes faster 
    - [AnkiConnect doesn't support multithreading], so interaction with its API probably can't be much faster (that's why I decided to use cache instead of checking if note exists using AnkiConnect API)
- caching (cache fill up while adding new words (not using existed cards))

[Anki]: https://en.wikipedia.org/wiki/Anki_(software)
[AnkiConnect]: https://ankiweb.net/shared/info/2055492159
[Free Dictionary API]: https://dictionaryapi.dev
[AnkiConnect doesn't support multithreading]: https://github.com/FooSoft/anki-connect/issues/2#issuecomment-271170024
[#1]: /../../issues/1