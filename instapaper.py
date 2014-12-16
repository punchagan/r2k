# Copyright (C) 2014 Puneeth Chaganti <punchagan at muse-amuse dot in>

"""Post links to Instapaper. """

import logging as _logging
import netrc

import requests

LOG = _logging.getLogger(__name__)


def add_url(feed, parsed, entry, guid, message):
    #_add_url(entry['link'], entry['title'])
    print(entry['link'])
    return message

def _add_url(url, title):
    username, _, password = netrc.netrc().authenticators('instapaper')
    instapaper_url = 'https://www.instapaper.com/api/add'

    requests.post(
        instapaper_url,
        data=dict(url=url, title=title),
        auth=(username, password)
    )

if __name__ == '__main__':
    _add_url('punchagan.muse-amuse.in', 'Test page')
