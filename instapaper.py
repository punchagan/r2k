# Copyright (C) 2014 Puneeth Chaganti <punchagan at muse-amuse dot in>

"""Post links to Instapaper. """

import logging as _logging
import netrc

import requests

LOG = _logging.getLogger(__name__)

def add_url(feed, parsed, entry, guid, message):
    _add_url(entry['link'], entry['title'])
    return message

def _add_url(url, title):
    username, _, password = netrc.netrc().authenticators('instapaper')
    instapaper_url = 'https://www.instapaper.com/api/add'

    response = requests.post(
        instapaper_url,
        data=dict(url=url, title=title),
        auth=(username, password)
    )

    if response.status_code//100 == 2:
        LOG.debug('Added url {}'.format(url))

    else:
        LOG.error('Failed to add url {} with message {}'.format(
            url, response.text)
        )

if __name__ == '__main__':
    _add_url('punchagan.muse-amuse.inx', 'Test page')
