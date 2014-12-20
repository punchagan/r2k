# r2k

Send rss feeds to the kindle

This repository contains various post processing hooks for rss2email, with the
eventual goal of sending RSS feeds to my kindle.

- `instapaper.py` sends feeds to Instapaper, which has an option of sending
  unread articles to the kindle.  But with a free account it only sends 10
  articles, and 50 with a paid account.  The post processing hook to use is:
  `instapaper add_article`

- `collect.py` and `digest.py` together create a `.mobi` book using `ebooklib`
  and `kindlegen`. The post processing hook to use is: `collect add_article`.
  (I currently use this hook).

The repository also has my config file with my subscriptions.

## Setup

I added the following crontab entry:

    0 12 * * * /path/to/r2k/r2k run -n && /path/to/r2k/r2k send_digest

`run -n` runs `rss2email` to get new entries for the subscribed feeds, without
sending any emails.  `send_digest` creates a mobi digest file, and sends it to
my kindle via email.

The `r2k` executable can be used to add/remove/list feeds, etc.
