#!/usr/bin/env python
"""Code to aggregate all articles in inbox/ and create a digest.mobi."""

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from os import listdir
from os.path import basename, expanduser, join
import smtplib
from subprocess import check_call

from rss2email.config import CONFIG


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
    mobi_path = 'digest-{}.mobi'.format
    check_call([kindlegen, path, '-o', mobi_path], cwd=OUTBOX)
    return join(OUTBOX, mobi_path)


def email_mobi(path):
    from_, to, message = _create_message()
    message = _attach_file(message, path)
    smtp = smtplib.SMTP()  # server = localhost
    smtp.sendmail(from_, to, message.as_string())
    smtp.close()


def _create_message(path):
    from_ = CONFIG['DEFAULT']['from']
    to = CONFIG['DEFAULT']['to']
    # fixme: try using 'Convert' and get rid of kindlegen?
    subject = 'Daily feed digest'
    message = MIMEMultipart(
        From=from_,
        To=to,
        Date=formatdate(localtime=True),
        Subject=subject
    )
    return from_, to, message


def _attach_file(message, path):
    with open(path, "rb") as f:
        message.attach(
            MIMEApplication(
                f.read(),
                Content_Disposition='attachment; filename="{}"'.format(basename(path))
            )
        )

    return message


def main():
    digest = create_digest_html()
    mobi = convert_html_to_mobi(digest)
    email_mobi(mobi)


if __name__ == '__main__':
    main()
