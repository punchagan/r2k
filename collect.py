# Copyright (C) 2014 Puneeth Chaganti <punchagan at muse-amuse dot in>

"""Collect all the metadata/data for the entries."""

import json
import logging as _logging
from os.path import abspath, dirname, join

LOG = _logging.getLogger(__name__)
HERE = dirname(abspath(__file__))

def get_article_html(feed, parsed, entry, guid, message):
    """Add article to the database.

    A post processing hook for rss2email, run on every new entry/article.

    """

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

# ### Private protocol ########################################################

def _read_db(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _write_db(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
