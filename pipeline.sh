#!/bin/bash

# This script takes two arguments: language and date.
# Usage example:
# ./pipeline.sh en 20191001

LNG=$1
DATE=$2

URLS=${LNG}wiki-$DATE-urls.txt
REVS=${LNG}wiki-$DATE-revisions.txt
DIFFS=${LNG}wiki-$DATE-diffs.pickle
SENTS=${LNG}wiki-$DATE-sents.pickle

python url_extractor.py -o $URLS -l $LNG -d $DATE
python filter.py -i $URLS -o $REVS -l $LNG
python diff.py -i $REVS -o $DIFFS -l $LNG
python sents.py -i $DIFFS -o $SENTS
python dataset.py -i $SENTS -l $LNG
