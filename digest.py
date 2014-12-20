#!/usr/bin/env python
"""Code to aggregate all articles in inbox/ and create a digest.mobi."""

import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate
from mimetypes import guess_type
from os.path import abspath, basename, dirname, exists, expanduser, join
import re
import shutil
import smtplib
from subprocess import check_call
from urllib.parse import urljoin, urlparse
from urllib.request import urlretrieve

from ebooklib import epub
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

_slugify_strip_re = re.compile(r'[^+\w\s-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')

ARTICLE_TEMPLATE = """
<h1>{title}</h1>
<div class="content">
    {content}
</div>
"""

def create_digest():
    digest = _create_digest_epub()
    mobi = _convert_to_mobi(digest)
    print('Digest at {}'.format(mobi))
    return mobi


def email_mobi(path):
    from_, to, message = _create_message(path)
    message = _attach_file(message, path)
    smtp = smtplib.SMTP()  # server = localhost
    smtp.connect()
    smtp.sendmail(from_, to, message.as_string())
    smtp.close()


def main(argv):
    USAGE = 'Usage: {} create_digest|send_digest.'.format(argv[0])
    if len(argv) != 2:
        print(USAGE)
    elif argv[1] == 'create_digest':
        create_digest()
    elif argv[1] == 'send_digest':
        email_mobi(create_digest())
    else:
        print(USAGE)


# ### Private protocol ########################################################

def _add_book_cover(book):
    path = _create_cover()
    book.set_cover("image.jpg", open(path, 'rb').read())


def _add_chapters(book, data):
    chapters = [
        _add_one_chapter(book, entry)

        for entry in

        sorted(data.values(), key=lambda x: x['date'], reverse=True)
    ]

    return chapters


def _add_images(book, html, base_url):
    tree  = fromstring(html)
    for node in tree.xpath('//*[@src]'):
        if node.tag != 'img':
            continue

        url = node.get('src')
        if _not_image_file(url) or _image_too_small(node):
            node.getparent().remove(node)

        else:
            file_name = _download_image(urljoin(base_url, url))
            node.set('src', file_name)
            img = epub.EpubImage(
                file_name=file_name,
                content=open(join(OUTBOX, file_name), 'rb').read()
            )
            book.add_item(img)

    return tostring(tree)


def _add_one_chapter(book, json_data):
    title = json_data['title']
    file_name = _slugify(title)+'.xhtml'
    content = str(_clean_js_and_styles(json_data['content']), encoding='utf8')
    content = ARTICLE_TEMPLATE.format(**{
        'content': content,
        'title': title
    })
    content = _add_images(book, content, json_data['url'])
    chapter = epub.EpubHtml(title=title, file_name=file_name, content=content)

    book.add_item(chapter)

    return chapter


def _add_navigation(book, chapters):
    book.toc = chapters

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    book.spine = ['nav'] + chapters


def _archive_json_data(path):
    new_path = join(OUTBOX, 'digest-{}.json'.format(DATE))
    shutil.move(path, new_path)


def _attach_file(message, path):
    with open(path, "rb") as f:
        message.attach(
            MIMEApplication(
                f.read(),
                Content_Disposition='attachment; filename="{}"'.format(basename(path))
            )
        )

    return message


def _clean_js_and_styles(html):
    cleaner = clean.Cleaner(javascript=True, style=True)
    return tostring(cleaner.clean_html(fromstring(html)))


def _convert_to_mobi(path):
    kindlegen = expanduser('~/bin/kindlegen')
    mobi_path = '{}.mobi'.format(TITLE)
    check_call([kindlegen, path, '-o', mobi_path], cwd=OUTBOX)
    return join(OUTBOX, mobi_path)


def _create_book_with_metadata():
    book = epub.EpubBook()

    # add metadata
    book.set_identifier(TITLE)
    book.set_title(TITLE_HUMAN)
    book.set_language('en')
    book.add_author('r2i - ebooklib')

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


def _create_digest_epub():
    from collect import _read_db

    book = _create_book_with_metadata()
    _add_book_cover(book)

    data_path = join(INBOX, 'digest.json')
    book_data = _read_db(data_path)
    chapters = _add_chapters(book, book_data)

    _add_navigation(book, chapters)

    epub_digest = join(OUTBOX, '{}.epub'.format(TITLE))
    epub.write_epub(epub_digest, book, {})

    _archive_json_data(data_path)

    return epub_digest


def _create_message(path):
    config = Config()
    with open(join(HERE, 'rss2instapaper.cfg')) as f:
        config.read_file(f)
    from_ = config['DEFAULT']['from']
    to = config['DEFAULT']['to']
    # fixme: try using 'Convert' and get rid of kindlegen?
    subject = TITLE_HUMAN
    message = MIMEMultipart(
        From=from_,
        To=to,
        Date=DATE_HUMAN,
        Subject=subject
    )
    return from_, to, message


def _download_image(url):
    name = basename(urlparse(url).path)
    path = join(OUTBOX, name)
    if not exists(path):
        urlretrieve(url, path)
    return name


def _image_too_small(node):
    height = int(re.match(r'\d+', node.get('height', '100')).group())
    width = int(re.match(r'\d+', node.get('width', '100')).group())
    return width * height < 10000


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


if __name__ == '__main__':
    import sys
    main(sys.argv)
