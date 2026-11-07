"""Resolve the original template's static TOC and caption lists from a rendered PDF."""
import argparse
import json
from pathlib import Path
import re
import unicodedata
import pypdfium2 as pdfium


def normalized(value):
    return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',value).replace('\u00ad','')).strip().casefold()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf',required=True,type=Path)
    parser.add_argument('--locators',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    doc=pdfium.PdfDocument(args.pdf)
    raw=[page.get_textpage().get_text_range() for page in doc]
    pages=[normalized(value) for value in raw]
    locators=json.loads(args.locators.read_text(encoding='utf-8'))
    first=normalized(locators['headings'][0]['text'])
    start=next(i for i,value in enumerate(raw) if i>=4 and first in [normalized(line) for line in value.splitlines()])
    result={'pages':len(doc),'anchors':{},'content_fingerprint':locators['content_fingerprint']}
    for group in ['headings','figures','tables']:
        for item in locators[group]:
            title=normalized(item['text'])
            begin=start-1 if item['anchor']=='kaggle_table_1' else start
            matches=[i+1 for i in range(begin,len(pages)) if title in pages[i]]
            if not matches:raise ValueError('Cannot resolve page for '+item['text'])
            result['anchors'][item['anchor']]=matches[0]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Resolved',len(result['anchors']),'headings and captions over',len(doc),'pages')


if __name__=='__main__':main()
