rss-digest tutorial
===================

This document will explain the basics of how to use rss-digest.

.. toctree::
   :maxdepth: 2
   :caption: Contents:


Installation
------------

TODO

Basic usage
-----------

rss-digest is primarily a command line tool. In order to use it you should have some basic familiarity with the command
line. Running rss-digest with the ``--help`` flag will output a message explaining the available arguments and options
(this also works with subcommands, eg, ``rss-digest profile add --help``).

Configuration
-------------

When installed, rss-digest will create a directory called ``rss-digest`` within the relevant user's general application
configuration directory. This is determined using the `appdirs <https://pypi.org/project/appdirs/>`_ library and will
depend on which operating system you are using. For example, on many Linux systems, the directory will be created at
``$HOME/.config/rss-digest``.

Within this directory you will find the following:

#. A file named ``config.ini``. This is the default main configuration file, which allows you to configure the behaviour
   of rss-digest globally.

#. A file named ``output.ini``. This is the default output configuration file, which allows you to configure how
   rss-digest should send the digests that it generates (for example, if you want to send digests by email, this file
   should contain SMTP server and login details).

#. A directory named ``profiles``. This directory will contain a directory for each profile that you create. Each such
   profile directory may contain a profile-specific ``config.ini`` and/or ``output.ini`` file. Values in those
   profile-specific files will override the global configuration.

Adding and configuring a profile
--------------------------------

The basic command to add a new profile is ``profile add``. So, if you wanted to add a new profile named "John", you
would run the following command:

.. code-block:: bash

    rss-digest profile add John

This will create an "empty" profile named "John", with no subscribed feeds and which uses the default application-level
configuration. If you want to configure the behaviour of rss-digest for this profile, you should copy (not move) the
global ``config.ini`` and/or ``output.ini`` to the profile directory and make the necessary changes.

.. note::
  Currently the only way to configure rss-digest is by manually editing the global or profile-specific ``config.ini``
  and ``output.ini`` files. There is no way to set configuration values directly from the command line.

Adding some feeds
-----------------

TODO

Running
-------

TODO

Configuration options
---------------------

TODO

Writing output templates
------------------------

rss-digest allows you to configure how output is formatted. Basically, output is generated using a
`jinja2 <https://jinja2docs.readthedocs.io/en/stable/>`_ template.

TODO