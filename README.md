# Lazy English Cards

This is an Anki plugin that makes it easy to add cards with English words, their pronunciation, explanation and usage examples. All you need is a wordlist.

This plugin uses [AnkiConnect] to add notes to Anki and [Free Dictionary API] to get info about required word.

## How to install

```
pip install -r requirements.txt
```

## How to use

Edit the `words.txt` file and paste in all words you want to add to your deck. You have to only put one word per line.

For next uses, you can overwrite existing words with new ones, or add new words anywhere in the file (words already processed have been cached, so you won't lose much time if you don't delete them). Script doesn't modify this file in any way, so you can keep your wordlist this way.

## To do

- make add-on from script
- add tests
- add UI

## Features
- plugin supports multutreading to add notes faster 
    - [AnkiConnect doesn't support multithreading], so interaction with its API probably can't be much faster (that's why I decided to use cache instead of checking if note exists using AnkiConnect API)
- caching (cache fill up while adding new words (not using existed cards))

[AnkiConnect]: https://ankiweb.net/shared/info/2055492159
[Free Dictionary API]: https://dictionaryapi.dev
[AnkiConnect doesn't support multithreading]: https://github.com/FooSoft/anki-connect/issues/2#issuecomment-271170024