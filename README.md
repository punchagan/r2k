# r2i

Send rss feeds to instapaper using rss2email.

This repository contains a simple post processing hook for rss2email that sends
urls to Instapaper using its simple API.

The repository also has my config file with my subscriptions.

With Instapaper's option of sending my unread articles to my Kindle
automatically, it makes a great reading tool.

## Setup

I added the following crontab entry:

    @hourly /path/to/executable/r2i run -n

`rss2email` doesn't send any emails when it is run with the `-n` option.

The `r2i` executable can be used to add/remove/list feeds, etc.
