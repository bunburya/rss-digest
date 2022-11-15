rss-digest tutorial
===================

This document will explain the basics of how to use rss-digest.

.. toctree::
   :maxdepth: 2
   :caption: Contents:


Installation
------------

rss-digest is not yet packaged, so the easiest way to install it is currently:

.. code-block:: bash

  git clone https://github.com/bunburya/rss-digest.git
  cd rss-digest
  pip3 install -e .


Basic usage
-----------

rss-digest is primarily a command line tool. In order to use it you should have some basic familiarity with the command
line. Running rss-digest with the ``--help`` flag will output a message explaining the available arguments and options
(this also works with subcommands, eg, ``rss-digest profile add --help``). The key sub-commands are discussed in more
detail below.


Configuration
-------------

When installed, rss-digest will create a directory called ``rss-digest`` within the relevant user's general application
configuration directory. This is determined using the `appdirs <https://pypi.org/project/appdirs/>`_ library and will
depend on which operating system you are using. For example, on many Linux systems, the directory will be created at
``$HOME/.config/rss-digest/``.

Within this directory you will find the following:

#. A file named ``config.toml``. This is the default main configuration file, which allows you to configure the
   behaviour of rss-digest globally.

#. A directory named ``profiles``. This directory will contain a directory for each profile that you create. Each such
   profile directory may contain a profile-specific ``config.toml`` file. Values in those profile-specific files will
   override the global configuration.

#. A directory named ``templates``, which contains the templates used by rss-digest to generate output (see below).

rss-digest also stores state (eg, information about previously fetched feeds) in an appropriate directory, again
determined by ``appdirs``. For example, on a Linux system this may be ``$HOME/.local/share/rss-digest/``.


Adding and configuring a profile
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The basic command to add a new profile is ``profile add``. So, if you wanted to add a new profile named "John", you
would run the following command:

.. code-block:: bash

  rss-digest profile add John

This will create an "empty" profile named "John", with no subscribed feeds and which uses the default application-level
configuration. If you want to configure the behaviour of rss-digest for this profile, you should copy (not move) the
global ``config.toml`` to the profile config directory and make the necessary changes.

.. note::
  Currently the only way to configure rss-digest is by manually editing the global or profile-specific ``config.toml``
  file. There is no way to set configuration values directly from the command line.


Configuration options
^^^^^^^^^^^^^^^^^^^^^

As mentioned above, rss-digest's behaviour is mainly configured through `TOML <https://toml.io>`_ configuration files.
When you install rss-digest, the config directory will contain a ``config.toml`` file which contains some basic default
configuration values. You can customise rss-digest's behaviour either by editing that file directly, or by placing
another ``config.toml`` file in the relevant profile's config directory.

Some of the main configuration options are:

* ``name``: The name of the recipient of the digest, to be used in the digest itself. If nothing is specified, the name
  of the profile is used.

* ``date_format``: A `strftime<https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior>`_-compatible
  format string to be used when referring to dates in the digest.

* ``time_format``: A strftime-compatible format string to be used when referring to times in the digest.

* ``datetime_format``: A strftime-compatible format string to be used when referring to datetimes (ie, a date and a time
  together) in the digest.

* ``max_displayed_feeds``: The maximum number of feeds to display under a single category in a digest.

* ``max_displayed_entries``: The maximum number of new entries to display for a single feed. At the end, a separate line
  will disclose how many new entries weren't displayed, and provide a general link to the feed's website.

* ``uncategorized_name``: The name to use when displaying the "category" of uncategorised feeds.

* ``timezone``: The user's local timezone, to be used when displaying times.

* ``template``: Which template to use to generate the output (see below). Currently, the supported templates are:

  * ``html``
  * ``markdown``
  * ``plaintext``

* ``content_type``: MIME type of the output (eg, text/plain or text/html)

* ``delivery_method``: Method to use to deliver output to the user. Currently, the only supported delivery method is
  ``sendmail_output``, which outputs the content of the digest in a format that can easily be piped to (or otherwise
  read by) ``sendmail -t`` (or a sendmail-like program which supports the ``-t`` option).

* ``email``: Required when the specified ``delivery_method`` involves sending the output by email (including
  ``sendmail_output``). Specifies the email address to send the digest to.


Adding and deleting feeds
-----------------

The ``feed`` command has certain sub-command (``add``, ``delete``, and ``list``) for working with feeds.

The ``add`` sub-command adds a feed and takes, at least, the name of the relevant profile and the URL for the feed.

.. code-block:: bash

  rss-digest feed add John https://bankunderground.co.uk/feed/

You can also provide the following arguments:

* ``--title``: The title of the feed (if not provided, the URL is used).
* ``--category``: The category to which the feed belongs.
* ``--fetch-title``: Fetch the feed title from the given URL (overrides a manually specified title).
* ``--test``: Test that the URL given is for a valid feed.
* ``--mark-read``: Mark all current entries as read, so that on the next run of rss-digest, only subsequent entries will
  be displayed.

For example:

.. code-block:: bash

  rss-digest feed add --title "Bank Underground" --category Economics --mark-read John https://bankunderground.co.uk/feed/

The ``delete`` sub-command takes the profile name and feed URL and, as you might expect, deletes the relevant feed.

.. code-block:: bash

  rss-digest feed delete John https://bankunderground.co.uk/feed/

Finally, the ``list`` sub-command lists all added feeds for the given profile.

.. code-block:: bash

  rss-digest feed list John

Internally, rss-digest stores feeds in an `OPML <https://en.wikipedia.org/wiki/OPML>`_ file called ``feeds.opml`` in the
profile config directory. If you have an appropriately formatted OPML file generated by another application, you can
save it in that location, rather than adding feeds manually. Similarly, you can copy that file for backup purposes or
use in other applications.

.. warning::
  When parsing or creating OPML files, rss-digest only recognises outline elements of type "category" or "rss", and only
  supports one level of categories (no sub-categories). Anything else will be ignored. If you provide rss-digest with an
  OPML file containing additional data or a more complex structure, it may be overwritten with a simplified OPML file
  generated by rss-digest itself.


Running
-------

The ``run`` command fetches all the feeds for the specified profile, compiles a digest of new or updated entries in each
feed, sends that digest using the output method specified in the relevant configuration and marks all fetched entries as
read.

.. code-block:: bash

  rss-digest run John

If the ``--forget`` option is passed, rss-digest will not mark new entries as read, so that they will be included again
on a subsequent run. This can be helpful for testing.

The effect of running rss-digest in this way will depend on the ``delivery_method`` specified in the configuration.
Where the ``sendmail_output`` method is specified, rss-digest will print the content of the digest to standard output,
preceded by ``To:`` and ``Subject:`` lines that can be read by a program like ``sendmail -t`` to send an email to the
user.


Writing output templates
------------------------

rss-digest allows you to configure how output is formatted. Output is generated using a
`jinja2 <https://jinja2docs.readthedocs.io/en/stable/>`_ template. Templates are stored in the ``templates`` directory
in the general configuration directory. Any file in that directory whose name does not begin with a ``\_`` will be
treated as a template that can be specified in the main configuration. For example, if you set the ``output`` option to
``plaintext`` in your ``config.toml``, rss-digest will look for a file called ``plaintext`` in the ``templates``
directory and use it to generate the output.

.. warning::
  jinja2 templates can contain arbitrary code which is executed when the output is generated. Therefore, you should not
  use untrusted templates.

A number of templates are provided with rss-digest. These are:

* ``plaintext``: To generate output as plain text.
* ``html``: To generate output as HTML.
* ``markdown``: To generate output as markdown.

It's also possible to create your own templates provided you have a little knowledge of Python and Jinja2. Consult the
`Jinja2 template design documentation <https://jinja2docs.readthedocs.io/en/stable/templates.html>`_ for help on how to
design your own templates.

Templates have access to the results of feed updates through a variable named ``ctx``. ``ctx`` is a
:class:`rss_digest.models.Context` object which contains information about what feeds were updated, what feeds weren't
updated and what errors were encountered in the update process. The documentation for :mod:`rss_digest.models` will tell
you what information you can (ultimately) access through the ``ctx`` variable and its attributes and properties. Looking
at the provided templates may also help you in creating your own.

Jinja2 allows you to effectively split a template over multiple files, by using
`template inheritance <https://jinja.palletsprojects.com/en/3.0.x/templates/#template-inheritance>`_,
`including files <https://jinja.palletsprojects.com/en/3.0.x/templates/#include>`_ or
`importing macros <https://jinja.palletsprojects.com/en/3.0.x/templates/#import>`_. If you want to create a file which
is not a final template itself but is extended/included/imported by a template, you can just give it a name beginning
with ``\_`` and place it in the ``templates`` directory.

.. note::
  Any whitespace in Jinja2 templates will be rendered in the output. Therefore, if you are creating a template for a
  format where whitespace is faithfully displayed to the end user (eg, plain text), then you should be careful about
  what whitespace you include. (HTML, for example, does not have this problem, as whitespace is ignored and spacing is
  controlled instead through HTML tags.)