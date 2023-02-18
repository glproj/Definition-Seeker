import bs4, re
from word_info_extractor import SESSION
from utils import TRENNBARE_PRÄFIXE
from ipdb import set_trace as s
INFLECTION_BASE_URL = 'https://de.wiktionary.org/wiki/Flexion:'

def break_german_verb(verb: str):
    for preffix in TRENNBARE_PRÄFIXE:
        pattern = rf"^({preffix})(\w+)"
        search = re.search(pattern, verb)
        try:
            return search.groups()
        except AttributeError:
            pass

class NotPreciseInflections:
    def __init__(self, word):
        url = INFLECTION_BASE_URL + word
        request = SESSION.get(url, timeout=0.8)
        self.word = word
        self.page = bs4.BeautifulSoup(request.text, 'html.parser')
        self.inflections = _get_inflections(self)
        
    def _get_inflections(self):
        every_pure_td= self.page.find_all('td', class_='', bgcolor='')
        texts_in_tds = [tag.text.strip() for tag in every_pure_td]
        #['sie werden hervorgetreten sein'] -> [['sie', 'werden', 'hervorgetreten', 'sein']]
        word_separated = [flexion.split(' ') for flexion in texts_in_tds]
        #planify list
        word_separated = [x for sub_list in word_separated for x in sub_list]
        #['sie', 'werden', 'hervorgetreten', 'sein'] -> [('hervor', 'getreten')]
        #the above behavior may be wrong, but it isn't that relevant for
        #example fetching. Just note how 'werden', 'sein', 'sie' disappear.
        ws_without_repetition = set([break_german_verb(x) for x in bruh2])
        

Inflections('hervortreten')


