# Copyright (C) 2014-2015 Puneeth Chaganti <punchagan at muse-amuse dot in>

"""Collect all the metadata/data for the entries."""

import logging as _logging
from os.path import abspath, dirname, join
import random
import time

from jsondb.db import Database

LOG = _logging.getLogger(__name__)
HERE = dirname(abspath(__file__))
CHOICES = '01234456789abcdef'

def add_article(feed, parsed, entry, guid, message):
    """Add article to the database.

    A post processing hook for rss2email, run on every new entry/article.

    """

    path = join(HERE, 'inbox', 'digest.json')
    db = Database(path)
    key = random_string()
    data = {
        'content': entry.get('summary', 'no summary'),
        'title': entry.get('title', 'no title'),
        'url': entry.get('link', 'no link'),
        'author': entry.get('author', ''),
        'blog': parsed.get('feed', {}).get('title', ''),
        'date_published': time.strftime('%Y-%m-%dT%H:%M:%S%z',
                                        entry.get('updated_parsed', time.localtime())),
        'date_added': time.strftime('%Y-%m-%dT%H:%M:%S%z', time.localtime()),
    }
    db.data(key=key, value=data)

    return message


def random_string(n=20):
    return ''.join(random.choice(CHOICES) for _ in range(n))
