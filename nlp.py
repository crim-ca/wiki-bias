import spacy
import argparse
from utils import check_lang

languages = ['af', 'ar', 'bg', 'bn', 'ca', 'cs', 'da', 'de', 'el', 'en', 'es',
             'et', 'fa', 'fi', 'fr', 'ga', 'he', 'hi', 'hr', 'hu', 'id', 'is',
             'it', 'ja', 'kn', 'ko', 'lt', 'lv', 'mr', 'nb', 'nl', 'pl', 'pt',
             'ro', 'ru', 'si', 'sk', 'sl', 'sq', 'sv', 'ta', 'te', 'th', 'tl',
             'tr', 'tt', 'uk', 'ur', 'vi', 'xx', 'zh']

exceptions = dict()
exceptions['bg'] = ['г.', 'т.', 'нар.', 'т.нар.', 'стр.', 'гр.', 'Св.',
                    'НУМТКН.', 'инж.', 'млн.', 'лв.', 'проф.', 'бул.', 'ул.',
                    'пл.', 'вр.', 'обл.', 'т.ч.', 'др.', 'сп.', 'виж.',
                    'т.е.', 'дн.', 'в.', 'чл.', 'тур.', 'напр.', 'мин.', 'яз.',
                    'ез.', 'с.', 'р.', 'пр.н.е.', 'ген.']


parser = argparse.ArgumentParser('language')
parser.add_argument('-l', '--lang', action="store", dest='lang',
                    required=True, type=check_lang,
                    help='Two-letter language tag to fetch')
args, _ = parser.parse_known_args()

if args.lang in languages:
    nlp = spacy.blank(args.lang.lower())
else:
    raise Exception("Language not supported by spaCy 2.1.3")

nlp.max_length = 2000000
sentencizer = nlp.create_pipe("sentencizer")
nlp.add_pipe(sentencizer)


def sbd(string):
    """
    Takes a string and returns a list of sentences
    longer than 5 tokens.
    string: param
    """
    doc = nlp(string)
    doc.is_parsed = True
    return [str(sent) for sent in list(doc.sents) if 5 < len(sent) < 300]
