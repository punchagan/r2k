# Copyright (C) 2014 Puneeth Chaganti <punchagan at muse-amuse dot in>

"""Generate a html from the digest with just the main article content.

Uses newspaper's capabilities to get the html for the article.

"""

import logging as _logging
from os.path import abspath, dirname, join
from urllib.parse import quote

from jinja2 import Environment, FileSystemLoader
from newspaper import Article

LOG = _logging.getLogger(__name__)
HERE = dirname(abspath(__file__))


def get_article_html(feed, parsed, entry, guid, message):
    # html = _get_article_html(entry['link'], entry['title'])
    html = entry['summary']
    path = join('inbox', quote(entry['link'], safe=''))
    template = _get_template()
    content = template.render(**{'html': html, 'entry': entry})
    with open(path, 'w') as f:
        f.write(content)


def _get_template():
    env = Environment(loader=FileSystemLoader(join(HERE, 'templates')))
    return env.get_template('article.html')


def _get_article_html(url, title):
    article = Article(url, title, keep_article_html=True)
    article.download()
    article.parse()
    if article.doc is None:
        LOG.error('Failed to parse {}'.format(url))
        html = ''

    else:
        html = str(article.article_html, encoding='utf-8')

    return html

if __name__ == '__main__':
    content = _get_article_html(
        'http://julien.danjou.info/blog/2014/python-distributed-membership-lock-with-tooz',
        'Distributed group management and locking in Python with tooz '
    )
    print(content)
