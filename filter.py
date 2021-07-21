import bz2
import sys
import os
import time
import argparse
import requests
from pov import POVProcessor
from StringBuilder import StringBuilder
from clint.textui import progress
from utils import check_lang


def download_file(url):
    local_filename = url.split('/')[-1]
    response = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        total_length = int(response.headers.get('content-length'))
        for chunk in progress.bar(response.iter_content(chunk_size=512),
                                  expected_size=(total_length / 512) + 1):
            if chunk:
                f.write(chunk)
    return local_filename


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputfile', action="store", dest='inputfile',
                        required=True,
                        help='Text file containing a list of paths to bz2 files to process')
    parser.add_argument('-o', '--outputfile', action="store", dest='outputfile',
                        required=True,
                        help='File path to output results')
    parser.add_argument('-l', '--lang', action="store", dest='lang',
                        required=True, type=check_lang,
                        help='Two-letter language tag to fetch')
    parser.add_argument('-r', '--remove', action="store_true",
                        help='Include to activate file deletion after processing')
    parser.add_argument('-s', '--separate_output', action="store_true",
                        help='Use the outputfile name as suffix to input file in order to generate separate '
                             'output files.')
    parser.add_argument('-v', '--verbose', action="store_true",
                        help='Include to log each article title')
    args = parser.parse_args()

    enc = 'UTF-8'
    log_file = False
    report_freq = 1000

    if args.verbose:
        log_file = True

    # Read the file list and run them
    files = open(args.inputfile).readlines()

    for infile in files:
        if not infile or infile == '':
            continue

        start = time.time()
        infile = infile.rstrip()
        output_file = args.outputfile

        # Download it if needed
        fname = os.path.basename(infile)
        if not os.path.exists(fname):
            print("Downloading file : " + fname)
            download_file(infile)
            print("Download finished!")
        else:
            print("File " + fname + " already downloaded!")
        print("Filtering...")

        if args.separate_output:
            output_file = fname + "." + output_file
            # Check if file already exist, delete it if so
            if os.path.exists(output_file):
                os.remove(output_file)

        if log_file:
            pov = POVProcessor("data/tags." + args.lang + ".txt", enc, output_file, fname + ".log")
        else:
            pov = POVProcessor("data/tags." + args.lang + ".txt", enc, output_file, None)

        cptPage = 0
        zip = bz2.BZ2File(fname)
        store = False
        fullpage = StringBuilder()
        for line in zip:
            line = line.decode(enc)

            if store:
                fullpage.append(line)
                if line == "  </page>\n":
                    # Process it
                    pov.extract(fullpage.to_string())
                    fullpage = StringBuilder()
                    store = False
                    cptPage += 1
                    if cptPage % report_freq == 0:
                        print(str(cptPage) + " pages processed...")

                elif line.startswith("    <ns>") and not line == "    <ns>0</ns>\n":
                    # Other types of pages
                    fullpage = StringBuilder()
                    store = False

            elif line == "  <page>\n":
                store = True
                fullpage = StringBuilder()
                fullpage.append(line)

        pov.write_tags()
        end = time.time()
        zip.close()

        # Delete the file
        if args.remove:
            os.remove(os.path.basename(fname))

        print("Execution time : " + str((end - start) / 60) + " min")


if __name__ == "__main__":
    main(sys.argv[1:])
