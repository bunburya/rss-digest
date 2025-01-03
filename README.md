# rss-digest: Generate digests of RSS and Atom feeds

rss-digest is a Python script for generating digests of subscribed RSS and Atom feeds (a "digest" being a single
document, email, etc which lists all the recent new or updated entries in each feed). Currently, it can send output via
SMTP, save it to a file or print it to standard output. The content and appearance of the digest is configurable using
Jinja2 templates; templates for HTML, plain text and markdown output are included by default.

For a detailed guide on how to install and use rss-digest is available, see the
[tutorial](https://bunburya.github.io/rss-digest). 
