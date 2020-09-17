#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import argparse
import editdistance
from nlp import sbd
from utils import to_pickle, check_lang
from normalize import clean_wiki, clean_punct, clean_tag
from typing import List, Text, Iterator, Dict


def preprocess(rev_pair: Text) -> Dict[str, str]:
    rev = dict()
    try:
        rev['tag'], rev['before'], rev['after'] = rev_pair.strip().split('\t')
        return rev
    except ValueError:
        return None


def redirected(dico: Dict) -> bool:
    """Considers a revision pair result of redirection/vandalism
    if the more recent version is shorter than 400 characters."""
    try:
        if len(dico['after']) < 400:
            return True
        else:
            return False
    except IndexError:
        return True


def unchanged(dico: Dict) -> bool:
    """If no sentences (longer than the cutoff of 5 tokens) were added
    or removed, consider the article unchanged."""
    return True if len(dico['add']) == len(dico['rem']) == 0 else False


def cross_check(x: List, y: List) -> List:
    return [i for i in x if i not in y]


def diff(dico: Dict) -> Dict[str, str]:
    """Split into sentences and extract the different ones.
    pov_pair: a tab-separated string with POV tag, old revision,
    new revision"""
    rev = dict()
    rev['tag'] = clean_tag(dico['tag'])
    rev['before'] = [sent for sent in sbd(clean_wiki(dico['before']))]
    rev['after'] = [sent for sent in sbd(clean_wiki(dico['after']))]
    rev['rem'] = cross_check(rev['before'], rev['after'])
    rev['add'] = cross_check(rev['after'], rev['before'])
    return rev


def filter_length(sents: List):
    return [sent for sent in sents if 5 < len(sent.split()) < 300]


def punct_diff(dico: Dict) -> Dict[str, str]:
    rev = dict()
    rev['tag'] = dico['tag']
    # further process the before and after state of the revision
    rev['before'] = [clean_punct(sent).lower() for sent in dico['before']]
    rev['after'] = [clean_punct(sent).lower() for sent in dico['after']]
    # remove too short or too long sentences
    rev['before'] = filter_length(rev['before'])
    rev['after'] = filter_length(rev['after'])
    # cross check to get updated lists of rem/add sentences
    rev['rem'] = cross_check(rev['before'], rev['after'])
    rev['add'] = cross_check(rev['after'], rev['before'])
    return rev


def outlier(dico: Dict) -> bool:
    """If more than 400 sentences are affected by a revision,
    consider the article as an outlier."""
    return True if len(dico['rem']) > 400 or len(dico['add']) > 400 else False


def insertions_only(dico: Dict) -> bool:
    return True if len(dico['rem']) == 0 < len(dico['add']) else False


def deletions_only(dico: Dict) -> bool:
    return True if len(dico['add']) == 0 < len(dico['rem']) else False


def min_distance(x: List, y: List) -> List:
    """x: sents to evaluate and filter
       y: sents to evaluate against"""
    min_dist = []
    for i in x:
        for j in y:
            # Do the sents differ in only one word?
            if editdistance.eval(i.split(), j.split()) == 1:
                # If so, is it a single character difference?
                if editdistance.eval(i, j) == 1:
                    min_dist.append(i)
    return min_dist


def filter_distance(dico: Dict) -> Dict[str, str]:
    rev = dict()
    rev['tag'] = dico['tag']
    rev['before'] = dico['before']
    rev['after'] = dico['after']

    rem_min = min_distance(dico['rem'], dico['add'])
    rev['rem'] = [sent for sent in dico['rem']
                  if sent not in rem_min]

    add_min = min_distance(dico['add'], dico['rem'])
    rev['add'] = [sent for sent in dico['add']
                  if sent not in add_min]
    return rev


def process(input_file) -> Iterator[Dict]:
    stats = dict()
    stats['total'] = 0
    stats['eligible'] = 0
    stats['redir./vandalism'] = 0
    stats['outliers'] = 0
    stats['tag removal'] = 0
    stats['punct./case'] = 0
    stats['deletions only'] = 0
    stats['insertions only'] = 0
    stats['spelling mistakes'] = 0
    stats['ignored, short'] = 0  # temporary, for EN only

    with open(input_file, 'r') as file:
        idx = 1
        for line in file:
            stats['total'] += 1
            if preprocess(line) is None:
                stats['ignored, short'] += 1
                continue
            revs = preprocess(line)  # split string into (tag, before, after)
            if redirected(revs):
                stats['redir./vandalism'] += 1
                idx += 1
                continue

            revs = diff(revs)  # transform string into a dictionary
            if unchanged(revs):
                stats['tag removal'] += 1
                idx += 1
                continue
            if outlier(revs):
                stats['outliers'] += 1
                idx += 1
                continue

            revs = punct_diff(revs)  # strip punctuation and lowercase
            if unchanged(revs):
                stats['punct./case'] += 1
                idx += 1
                continue
            if insertions_only(revs):
                stats['insertions only'] += 1
                idx += 1
                continue
            if deletions_only(revs):
                stats['deletions only'] += 1
                idx += 1
                continue

            revs = filter_distance(revs)  # remove L=1 sentences from rem & add
            if unchanged(revs):
                stats['spelling mistakes'] += 1
                idx += 1
                continue

            stats['eligible'] += 1

            idx += 1
            yield revs
    print(*[f"{key}: {value}" for key, value in stats.items()], sep='\n')


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputfile', action="store", dest='inputfile',
                        required=True,
                        help='Text file containing a list of paths to bz2 files to process')
    parser.add_argument('-o', '--outputfile', action="store", dest='outputfile',
                        required=True,
                        help='Suffix to add to input file in order to output results')
    parser.add_argument('-l', '--lang', action="store", dest='lang',
                        required=True, type=check_lang,
                        help='Two-letter language tag to fetch')
    args = parser.parse_args()

    print(f'Processing file {args.inputfile}')
    data = [d for d in process(args.inputfile)]
    to_pickle(data, args.outputfile)


if __name__ == "__main__":
    main(sys.argv[1:])
