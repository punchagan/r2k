# Copyright (C) 2014 Puneeth Chaganti <punchagan at muse-amuse dot in>

"""Collect all the metadata/data for the entries."""

import json
import logging as _logging
from os.path import join

from lxml.html import clean, fromstring, tostring

from utils import HERE

LOG = _logging.getLogger(__name__)


def get_article_html(feed, parsed, entry, guid, message):
    html = _clean_js_and_styles(entry['summary'])
    path = join(HERE, 'inbox', 'digest.json')
    data = _read_db(path)
    data[guid] = {
        'content': str(html, encoding='utf-8'),
        'title': entry['title'],
        'url': entry['link'],
        'author': entry['author'],
        'updated': entry['updated'],
    }
    _write_db(path, data)


def _clean_js_and_styles(html):
    cleaner = clean.Cleaner(javascript=True, style=True)
    return tostring(cleaner.clean_html(fromstring(html)))


def _read_db(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _write_db(path, data):
    with open(path, 'w') as f:
        json.dump(data, f)

if __name__ == '__main__':
    pass
