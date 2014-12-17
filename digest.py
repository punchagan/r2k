#!/usr/bin/env python
"""Code to aggregate all articles in inbox/ and create a digest.mobi."""

from os import listdir
from os.path import expanduser, join
from subprocess import check_call

from utils import get_template, HERE

INBOX = join(HERE, 'inbox')
OUTBOX = join(HERE, 'outbox')

def create_digest_html():
    posts = []
    for f in listdir(INBOX):
        if f != '.keep':
            with open(join(INBOX, f)) as g:
                posts.append(g.read())

    template = get_template('digest.html')
    with open(join(OUTBOX, 'digest.html'), 'w') as f:
        f.write(template.render(posts=posts))

    return f.name


def convert_html_to_mobi(path):
    kindlegen = expanduser('~/bin/kindlegen')
    mobi_path = 'digest.mobi'
    check_call([kindlegen, path, '-o', mobi_path], cwd=OUTBOX)
    return mobi_path

def email_mobi(path):
    pass


def main():
    digest = create_digest_html()
    mobi = convert_html_to_mobi(digest)
    email_mobi(mobi)

if __name__ == '__main__':
    main()
