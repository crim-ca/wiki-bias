import re
import sys
import urllib.request
import argparse
from utils import check_date, check_lang


def main(argv):
    """
    Fetch the wikipedia dump page and extract the (list of) file(s) containing
    the full revision history of all articles and output it to a single file
    for the next step.
    :param argv: commandline parameters for the execution
    :return:
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--outputfile', action="store", dest='outpufile',
                        required=True,
                        help='Full path to output the url list into')
    parser.add_argument('-l', '--lang', action="store", dest='lang',
                        required=True, type=check_lang,
                        help='Two-letter language tag to fetch')
    parser.add_argument('-d', '--date', action="store", dest='date',
                        required=True, type=check_date,
                        help='The exact wikipedia archive date (YYYMMDD)')
    args = parser.parse_args()
    baseurl = 'https://dumps.wikimedia.org'

    # Download page
    response = urllib.request.urlopen(baseurl + "/" + args.lang + "wiki/"
                                      + args.date + "/")
    page = response.read()

    # Fetch the matching url for the complete page edit history in bz2 format
    linkpattern = r"(\/" + args.lang + r"wiki\/" + args.date + r"\/" + \
                  args.lang + "wiki-" + args.date + \
                  r"-pages-meta-history\d{0,3}\.xml(-p\d{1,9}p\d{1,9})?\.bz2)"
    matches = re.findall(linkpattern, page.decode("UTF-8"))

    # Write them to the output file
    cpt = 0
    with open(args.outpufile, "w+") as f:
        for m in matches:
            cpt += 1
            f.write(baseurl + m[0] + "\n")

    print(str(cpt) + " url(s) generated")


if __name__ == "__main__":
    main(sys.argv[1:])
