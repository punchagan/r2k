# Copyright (C) 2014-2015 Puneeth Chaganti <punchagan at muse-amuse dot in>

"""Collect all the metadata/data for the entries."""

import logging as _logging
from os.path import abspath, dirname, join
import time

from jsondb.db import Database

LOG = _logging.getLogger(__name__)
HERE = dirname(abspath(__file__))

def add_article(feed, parsed, entry, guid, message):
    """Add article to the database.

    A post processing hook for rss2email, run on every new entry/article.

    """

    path = join(HERE, 'inbox', 'digest.json')
    db = Database(path)
    key = guid or entry['link'] or entry['title']
    data = {
        'content': entry['summary'],
        'title': entry['title'],
        'url': entry['link'],
        'author': entry.get('author', ''),
        'blog': parsed.get('feed', {}).get('title', ''),
        'date_published': time.strftime('%Y-%m-%dT%H:%M:%S%z', entry['updated_parsed']),
        'date_added': time.strftime('%Y-%m-%dT%H:%M:%S%z', time.localtime()),
    }
    db.data(key=key, value=data)

    return message
