#!/usr/bin/env python
# Copyright (C) 2014-2015 Puneeth Chaganti <punchagan at muse-amuse dot in>
"""Code to aggregate all articles in inbox/ and create a digest.mobi."""

import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from mimetypes import guess_type
import os
from os.path import abspath, basename, dirname, exists, expanduser, join, splitext
import re
import smtplib
from subprocess import Popen
import time
from urllib.parse import quote, urljoin, urlparse
from urllib.request import urlretrieve

from ebooklib import epub
from jsondb.db import Database
from lxml.html import clean, fromstring, tostring
from rss2email.config import Config
from PIL import Image, ImageDraw

HERE = dirname(abspath(__file__))
INBOX = join(HERE, 'inbox')
OUTBOX = join(HERE, 'outbox')
DATE = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
TITLE = 'digest-{}'.format(DATE)
DATE_HUMAN = formatdate(localtime=True)
TITLE_HUMAN = 'Daily Digest - {}'.format(DATE_HUMAN)

_slugify_strip_re = re.compile(r'[^\w\s-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')

CONFIG = Config()
with open(join(HERE, 'r2k.cfg')) as f:
    CONFIG.read_file(f)

WEBSERVER = os.getenv('GOOVER_SERVER', CONFIG['DEFAULT']['goover-server'])


ARTICLE_TEMPLATE = """
<h1>{{title}}</h1>
<div>
    <span class="author">{{author}}</span>
    <span class="date">{{date}}</span>
    <span class="blog">{{blog}}</span>
</div>
<div class="content">
    {{content}}
</div>
<div class="r2k-actions">
    <ul style="display: inline;">
        <li><a href="{webserver}/edit?id={{id}}&tag=read">Mark ARTICLE as read</a></li>
        <li><a href="{webserver}/edit?id={{id}}&tag=!read">Mark ARTICLE as UNread</a></li>
        <li><a href="{webserver}/edit?{{all_ids}}&tag=read">Mark DIGEST as read</a></li>
        <li><a href="{webserver}/edit?{{all_ids}}&tag=!read">Mark DIGEST as UNread</a></li>
    </ul>
<div>
""".format(webserver=WEBSERVER)

def create_digest(path):
    print('Using {} to create digest.'.format(path))
    epub, entries = _create_digest_epub(path)
    mobi = _convert_to_mobi(epub)
    _update_last_digest_timestamp(path)
    _mark_entries_as_digested(path, entries)

    if exists(mobi):
        print('Digest at {}'.format(mobi))

    else:
        print('Digest creation failed')
        mobi = None
    return mobi


def email_mobi(path):
    from_, to, message = _create_message(path)
    smtp = smtplib.SMTP()  # server = localhost
    smtp.connect()
    smtp.sendmail(from_, to, message.as_string())
    smtp.close()


def main(argv):
    USAGE = 'Usage: {} create_digest|send_digest [path-to-json].'.format(argv[0])
    if len(argv) < 2:
        print(USAGE)

    elif argv[1] == 'create_digest':
        path = ''.join(argv[2:]) or join(INBOX, 'digest.json')
        create_digest(path)

    elif argv[1] == 'send_digest':
        path = ''.join(argv[2:]) or join(INBOX, 'digest.json')
        mobi = create_digest(path)
        if mobi is not None:
            email_mobi(mobi)
    else:
        print(USAGE)


# ### Private protocol ########################################################

def _add_book_cover(book):
    path = _create_cover()
    book.set_cover("image.jpg", open(path, 'rb').read())
    book.spine.insert(0, 'cover')


def _add_chapters(book, data):
    data = sorted(
        [each for each in data.items()],
        key=lambda x: x[1]['date_published'],
        reverse=True
    )

    keys = '&'.join('id={}'.format(quote(key)) for key, _ in data)
    chapters = [_add_one_chapter(book, keys, *entry) for entry in data]

    return chapters


def _add_images(book, html, base_url):
    tree  = fromstring(html)
    for node in tree.xpath('//*[@src]'):
        if node.tag not in ('img', 'video'):
            continue

        url = node.get('src')
        if node.tag == 'video' or _not_image_file(url) or _image_too_small(node):
            node.getparent().remove(node)

        else:
            file_name = _download_image(urljoin(base_url, url))
            if file_name is None:
                node.getparent().remove(node)

            else:
                node.set('src', file_name)
                img = epub.EpubImage(
                    file_name=file_name,
                    content=open(join(OUTBOX, file_name), 'rb').read()
                )
                book.add_item(img)

    return tostring(tree)


def _add_one_chapter(book, all_ids, id_, json_data):
    title = json_data['title']
    file_name = _slugify(title)+'.xhtml'
    content = _clean_js_and_styles(json_data['content'])
    content = ARTICLE_TEMPLATE.format(**{
        'id': quote(id_),
        'all_ids': all_ids,
        'content': content,
        'title': title,
        'author': json_data['author'],
        'date': json_data['date_published'],
        'blog': json_data['blog'],
    })
    content = _add_images(book, content, json_data['url'])
    content = _convert_urls_to_full(content, json_data['url'])
    chapter = epub.EpubHtml(title=title, file_name=file_name, content=content)

    book.add_item(chapter)

    return chapter


def _add_navigation(book, chapters):
    book.toc = chapters

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    book.spine += ['nav'] + chapters


def _clean_js_and_styles(html):
    cleaner = clean.Cleaner(javascript=True, style=True)

    try:
        html = str(
            tostring(cleaner.clean_html(fromstring(html))), encoding='utf8'
        )

    except Exception:
        html = 'Failed to clean js and styles.'

    return html


def _convert_to_mobi(path):
    kindlegen = expanduser('~/bin/kindlegen')
    mobi_path = basename(path.replace('.epub', '.mobi'))
    Popen([kindlegen, path, '-o', mobi_path], cwd=OUTBOX).wait()
    return join(dirname(path), mobi_path)


def _convert_urls_to_full(html, base_url):
    tree  = fromstring(html)
    for node in tree.xpath('//*[@href]'):
        url = node.get('href')
        parsed_url = urlparse(url)
        scheme = parsed_url.scheme
        path = parsed_url.path
        fragment = parsed_url.fragment

        if node.tag not in ('a') or scheme:
            continue

        elif url.startswith('//'):
            # Kindlegen doesn't like urls like //xkcd.com/131
            url = 'http:{}'.format(url)

        elif not scheme and (path or fragment):
            url = urljoin(base_url, url)

        node.set('href', url)

    return tostring(tree)


def _create_book_with_metadata():
    book = epub.EpubBook()

    # add metadata
    book.set_identifier(TITLE)
    book.set_title(TITLE_HUMAN)
    book.set_language('en')
    book.add_author('r2k')

    return book


def _create_cover():
    # http://kindlegen.s3.amazonaws.com/AmazonKindlePublishingGuidelines.pdf
    X, Y = 1600, 2560
    # We draw a scaled down image, since increasing font size is a pain.
    size = (X//4, Y//4)
    im = Image.new('RGB', size)
    draw = ImageDraw.Draw(im)

    color = (255, 255, 255)
    font = draw.getfont()
    x, y = font.getsize(TITLE_HUMAN)
    position = ((size[0]-x)//2, size[1]//3)
    draw.text(position, TITLE_HUMAN, fill=color)

    cover_path = join(OUTBOX, 'cover.jpg')
    with open(cover_path, 'wb') as f:
        # Scale up the image before save
        im.resize((X, Y)).save(f, format='jpeg')

    return cover_path


def _create_digest_epub(path):
    book = _create_book_with_metadata()
    _add_book_cover(book)

    entries = _get_entries(path)
    chapters = _add_chapters(book, entries)

    _add_navigation(book, chapters)

    epub_digest = join(OUTBOX, '{}.epub'.format(TITLE))
    epub.write_epub(epub_digest, book, {})

    return epub_digest, entries


def _create_message(path):
    message = MIMEMultipart()
    # fixme: try using 'Convert' and get rid of kindlegen?
    message['Subject'] = TITLE_HUMAN
    message['From'] = from_ = CONFIG['DEFAULT']['from']
    message['To'] = to = CONFIG['DEFAULT']['to']
    message.preamble = TITLE_HUMAN

    # Attach file
    with open(path, 'rb') as fp:
        mobi = MIMEBase('application', 'x-mobipocket-ebook')
        mobi.set_payload(fp.read())
    encoders.encode_base64(mobi)
    mobi.add_header('Content-Disposition', 'attachment', filename=basename(path))
    message.attach(mobi)

    return from_, to, message


def _download_image(url):
    name, ext = splitext(basename(urlparse(url).path))
    name = '{}{}'.format(_slugify(name), ext)
    path = join(OUTBOX, name)
    if not exists(path):
        try:
            urlretrieve(url, path)
        except Exception:
            name = None

    return name


def _get_entries(db_path):
    db = Database(db_path)
    data = db.data()

    last_digest_timestamp = data.pop('last-digest-timestamp', None)
    if last_digest_timestamp is not None:
        data = {
            guid: entry for guid, entry in data.items()
            if entry['date_added'] > last_digest_timestamp
        }

    return data


def _image_too_small(node):
    height = int(re.match(r'\d+', node.get('height', '100')).group())
    width = int(re.match(r'\d+', node.get('width', '100')).group())
    return width * height < 10000


def _mark_entries_as_digested(db_path, entries):
    db = Database(db_path)

    for key, value in entries.items():
        tags = value.setdefault('tags', [])
        if 'digest' not in tags:
            tags.append('digest')

        db.data(key=key, value=value)


def _not_image_file(url):
    mt = guess_type(urlparse(url).path)[0]
    return True if mt is None else not mt.startswith('image')


def _slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    From Django's "django/template/defaultfilters.py".

    >>> print(slugify('\xe1\xe9\xed.\xf3\xfa'))
    aeiou

    >>> print(slugify('foo/bar'))
    foobar

    >>> print(slugify('foo bar'))
    foo-bar

    copied from Nikola's utils.

    """

    value = str(_slugify_strip_re.sub('', value).strip().lower())
    return _slugify_hyphenate_re.sub('-', value)


def _update_last_digest_timestamp(path):
    db = Database(path)
    db.data(
        key='last-digest-timestamp',
        value=time.strftime('%Y-%m-%dT%H:%M:%S%z', time.localtime())
    )


if __name__ == '__main__':
    import sys
    main(sys.argv)
