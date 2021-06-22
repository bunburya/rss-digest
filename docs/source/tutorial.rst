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

There are two main configuration files: ``config.ini``, which contains options for configuring the behaviour of
rss-digest generally, and ``output.ini``, which contains options relating to how rss-digest should send generated
output. ``output.ini`` is a separate file because it may contain sensitive information, such as email addresses and
login details.

As the names suggest, both configuration files are in the `INI <https://en.wikipedia.org/wiki/INI_file>`_ format. INI
files are divided into sections, denoted in square brackets. ``config.ini`` only has one section, ``[defaults]``, which
contains all configuration options. You can take a look at the skeleton ``config.ini`` file to familiarise yourself
with the available options, what they do and their default values.


Writing output templates
------------------------

rss-digest allows you to configure how output is formatted. Basically, output is generated using a
`jinja2 <https://jinja2docs.readthedocs.io/en/stable/>`_ template. Templates are stored in the ``templates`` directory
in the general configuration directory. Any file in that directory whose name does not begin with a ``\_`` will be
treated as a template that can be specified in the main configuration. For example, if you set the ``output`` option to
``plaintext`` in your ``config.ini``, rss-digest will look for a file called ``plaintext`` in the ``templates``
directory and use it to generate the output.

.. warning::
  jinja2 templates can contain arbitrary code which is executed when the output is generated. Therefore, you should not
  use untrusted templates.

A number of templates are provided with rss-digest. These are:

* ``plaintext``: To generate output as plain text.
* ``html``: To generate output as HTML.
* ``markdown``: To generate output as markdown.
* ``rss``: To generate an RSS file with all updated entries.

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

TODO