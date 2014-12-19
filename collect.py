# Copyright (C) 2014 Puneeth Chaganti <punchagan at muse-amuse dot in>

"""Collect all the metadata/data for the entries."""

import json
import logging as _logging
from os.path import join
from utils import HERE

LOG = _logging.getLogger(__name__)


def get_article_html(feed, parsed, entry, guid, message):
    path = join(HERE, 'inbox', 'digest.json')
    data = _read_db(path)
    data[guid] = {
        'content': entry['summary'],
        'title': entry['title'],
        'url': entry['link'],
        'author': entry['author'],
        'updated': entry['updated'],
    }
    _write_db(path, data)


def _read_db(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _write_db(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

if __name__ == '__main__':
    pass
