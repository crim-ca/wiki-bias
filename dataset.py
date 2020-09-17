import sys
import random
import argparse
from utils import unpickle, to_text_file, check_lang
from typing import List


def label(sentences: List, label: str, prefix: str, separator: str) -> List:
    return [prefix + label + separator + s for s in sentences]


def split_dataset(adds: List, rems: List, lang):
    dataset = adds + rems
    dataset.sort()
    random.seed(230)
    random.shuffle(dataset)

    split_1 = int(0.8 * len(dataset))
    split_2 = int(0.9 * len(dataset))
    train = dataset[:split_1]
    dev = dataset[split_1:split_2]
    test = dataset[split_2:]
    to_text_file(train, lang.upper() + '-train.txt')
    to_text_file(dev, lang.upper() + '-dev.txt')
    to_text_file(test, lang.upper() + '-test.txt')


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputfile', action="store", dest='inputfile',
                        required=True,
                        help='Text file containing a list of paths to bz2 files to process')
    parser.add_argument('-l', '--lang', action="store", dest='lang',
                        required=True, type=check_lang,
                        help='Two-letter language tag to fetch')
    parser.add_argument('-p', '--prefix', action="store", dest='prefix', default='',
                        help='Classifier-specific label prefix, e.g. __label__')
    args = parser.parse_args()

    data = unpickle(args.inputfile)
    add = label(data['add'], label='neutral', prefix=args.prefix, separator='\t')
    rem = label(data['rem'], label='biased', prefix=args.prefix, separator='\t')
    split_dataset(add, rem, args.lang)


if __name__ == '__main__':
    main(sys.argv[1:])
