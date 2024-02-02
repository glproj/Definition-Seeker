# Definition-Seeker
CLI tool to get useful information about words with speed and lightness. Made to be used with Anki (although it is not an Anki extension).

# Installation
Clone the project:
```
git clone https://github.com/glproj/Definition-Seeker.git
```
Cd to project directory:
```
cd Definition-Seeker
```
Create and activate virtual environment with pipenv:
```
pipenv install
pipenv shell
```
Run the script:
```
python source/main.py
```
# Usage
## Basic Usage
Once you execute the main.py script, you'll be met with something like this
```
Current language: de
q=quit
dwds=dwds' definition for the previous word
duden=duden's definition for the previous word
save=save previous word for later use
images=download 3 images related to the previous word. You can paste them using pause_break
examples=shows examples of previous word from the books in the configfile
lang {language code}=change language.Available languages: en, de
------------------------------------------------------------------------
Word: 
```
You can now input any (german, in this case) word and get useful information like definitions and examples.

## Copy and Paste
The script sends phonetic information to your clipboard each time you search for a word:

https://user-images.githubusercontent.com/91835436/220395855-f5a316b5-a969-4e28-81aa-fc2adffb1f45.mp4

This behavior doesn't apply when searching in sources other than the primary source. If you search for Gnade with dwds, for example, the output will be this:

```
Gnade
Phonetics: ˈgnaːdə https://media.dwds.de/dwds2/audio/031/die_Gnade.mp3
[1] christliche Theologie unverbrüchliche, bedingungslose Liebe, Zuwendung und Treue Gottes zu den sündigen und unvollkommenen Menschen
```
But no phonetic info will be sent to your clipboard. Copying and pasting the link on the dwds output will get you the same result as in the video (at least when using xterm).

## Commands
The commands you can use are already described on the start screen, so here I'll just describe what "previous word" means.
If you input the word "Exegese", then "Exegese" will turn into the previous word, so that if you run "dwds" the program will fetch informations about Exegese in the dwds dictionary. If the word isn't available in de.wiktionary.org, however, then the previous word will not change at all. But this isn't that big of a deal when you can just run "dwds {word}" to get the desired result.

# Languages
## Supported Languages
English, German, French, Russian, Latin, Portuguese
