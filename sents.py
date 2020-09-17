import sys
import argparse
import random
from utils import to_pickle, unpickle
from typing import List, Dict


def get_sentences(data: Dict, sentence_class: str):
    sentences = []
    for dico in data:
        if sentence_class in dico:
            sentences.extend(dico[sentence_class])
        else:
            raise Exception('No such sentence class in the dictionary!')
    return sentences


def remove_duplicates(adds: List, rems: List):
    new_adds = set(adds) - set(rems)
    new_rems = set(rems) - set(adds)
    return (list(new_adds), list(new_rems))


def balance_classes(adds: list, rems: list, others: List) -> List:
    difference = len(rems) - len(adds)
    selection = set()
    while len(selection) < difference:
        selection.add(random.choice(others))
    return list(selection)


def get_classes(data: Dict):
    added = get_sentences(data, 'add')
    removed = get_sentences(data, 'rem')
    unchanged = get_sentences(data, 'after')

    # Remove duplicates within and across classes
    add, rem = remove_duplicates(added, removed)
    print('added =', len(add), '+ unchanged =', len(rem)-len(add))
    print('removed =', len(rem))

    # Balance the classes
    if len(add) < len(rem):
        unchanged = list(set(unchanged) - set(add))
        add.extend(balance_classes(add, rem, unchanged))
    print('total =', len(rem+add))
    return (add, rem)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputfile', action="store", dest='inputfile',
                        required=True,
                        help='Text file containing a list of paths to bz2 files to process')
    parser.add_argument('-o', '--outputfile', action="store", dest='outputfile',
                        required=True,
                        help='Suffix to add to input file in order to output results')
    args = parser.parse_args()

    print('Extracting and labeling the sentences...')
    sentences = dict()
    data = unpickle(args.inputfile)
    sentences['add'], sentences['rem'] = get_classes(data)
    to_pickle(sentences, args.outputfile)


if __name__ == '__main__':
    main(sys.argv[1:])
