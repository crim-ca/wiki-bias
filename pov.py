import logging
import io
import xml.etree.ElementTree as ET
import re
import os


class POVProcessor(object):
    """
    Process a full revision history for a wikipedia page from the database dump and extract the revision tagged with
    the list found in the tag file.
    """

    default_tags = 'NPOV\nEditorial'

    def __init__(self, tags_file: str, enc: str, output_file: str, logfile: str):
        if os.path.exists(os.path.join(os.getcwd(), tags_file)):
            with open(os.path.join(os.getcwd(), tags_file), encoding=enc) as f:
                tags = [re.escape(tag) for tag in f.read().strip().split('\n')]
        else:
            print(f'{tags_file} not found, using default tags' )
            tags = [re.escape(tag) for tag in POVProcessor.default_tags.split('\n')]
        self.regex = r'(?i){{((' + r'|'.join(tags) + r'))(\|[^}]+)?}}' # FIXME: why ((..))
        self.match = lambda x: re.search(self.regex, str(x.find('text').text))
        self.all_tags = re.compile(r"{{([^|}]+)}}")

        self.output = open(output_file, 'a', encoding=enc)
        self.output_tags = open(output_file + '.alltags.txt', 'a', encoding=enc)
        self.enc = enc
        self.logit = False
        if logfile:
            logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler(logfile, 'w+', 'utf-8')])
            self.logit = True
        self.tags = dict()
        self.tag_size_limit = 45

    def write_tags(self):
        for tag in self.tags:
            self.output_tags.write(tag + '\t' + str(self.tags[tag]) + '\n')

    def normalize_ws(self, text: str):
        return re.sub(r'\s+', ' ', text).strip()

    def extract(self, page: str):
        if self.logit:
            logging.info("Page : " + page[page.find("<title>") + 7:page.find("</title>")])
        pov = None
        no_pov = None
        pov_tag = ""

        # Look for all tags
        # for x in re.finditer(self.all_tags, page):
        #     pos = page.find('|', x.span()[0]+2, x.span()[1] - x.span()[0] - 4)
        #     tg = page[x.span()[0]+2:x.span()[0]+2 + max(pos, min(self.tag_size_limit, x.span()[1] - x.span()[0] - 4))]
        #     tg = tg.lower().strip() .replace('\n', ' ')
        #     if tg not in self.tags:
        #         self.tags[tg] = 0
        #     self.tags[tg] = self.tags[tg] + 1

        # Based on http://effbot.org/elementtree/iterparse.htm
        context = ET.iterparse(io.StringIO(page), events=("start", "end"))
        context = iter(context)
        _, root = context.__next__()

        for event, elem in context:
            if event == 'end':
                if elem.tag == 'revision' and elem.find('parentid') is None:
                    root.clear()
                elif elem.tag == 'revision' and elem.find('text').text:
                    if self.match(elem) is None and pov is None:
                        root.clear()
                    elif self.match(elem) is not None:
                        pov_tag = elem.find('text').text[re.search(self.regex, elem.find('text').text).regs[0][0]:
                                                         re.search(self.regex, elem.find('text').text).regs[0][1]]
                        pov = self.normalize_ws(elem.find('text').text) or ''
                        root.clear()
                    elif self.match(elem) is None and pov is not None:
                        tag_found = self.match(elem)
                        no_pov = self.normalize_ws(elem.find('text').text)
                        # print(pov_tag + '\t' + pov + '\t' + no_pov)
                        self.output.write(pov_tag.replace('\t', ' ').replace('\n', ' ') + '\t' +
                                          pov.replace('\t', ' ').replace('\n', ' ') + '\t' +
                                          no_pov.replace('\t', ' ').replace('\n', ' ') + '\n')
                        pov = None
                        pov_tag = None
                        root.clear()
