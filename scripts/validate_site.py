#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]
        self.scripts=[]
        self.styles=[]
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag=='a' and d.get('href'): self.links.append(d['href'])
        if tag=='script' and d.get('src'): self.scripts.append(d['src'])
        if tag=='link' and d.get('href'): self.styles.append(d['href'])

def fail(msg):
    print('FAIL:', msg)
    raise SystemExit(1)

html_path=DOCS/'index.html'
if not html_path.exists(): fail('docs/index.html missing')
text=html_path.read_text(encoding='utf-8')
for needle in ['TinySkiff ESP32-S3 Lab','Project browser','Official ZIP archive','site-data']:
    if needle not in text: fail(f'missing marker {needle!r}')
match=re.search(r'<script id="site-data" type="application/json">(.*?)</script>', text, re.S)
if not match:
    fail('embedded JSON missing')
assert match is not None
data=json.loads(match.group(1).replace('<\\/','</'))
checks={
  'projectsC': 40,
  'projectsPython': 20,
  'libraries': 20,
  'pdfs': 20,
}
for key,min_count in checks.items():
    n=len(data.get(key,[]))
    print(key,n)
    if n < min_count: fail(f'{key} too small: {n}')
parser=LinkParser(); parser.feed(text)
for rel in parser.scripts + parser.styles:
    if rel.startswith('./') and not (DOCS/rel[2:]).exists(): fail(f'missing asset {rel}')
for img in ['assets/Super.jpg','assets/ESP32S3_Pinout.png']:
    if not (DOCS/img).exists(): fail(f'missing image {img}')
print('OK site validation passed')
