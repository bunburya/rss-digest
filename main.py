#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO: 
# - add proper command parsing, including way to add profiles, feeds, etc
# - add propert interface for editing feed lists

import logging

from sys import argv

from cli_ui import CLInterface
from rss_digest import RSSDigest

def launch_cli_ui(app):
    
    ui = CLInterface(app)
    ui.repl()

def run_profile(app, profile):
    
    app.email_profile_name(profile)

def dryrun_profile(app, profile):
    
    app.email_profile_name(profile, update=False)
    
if __name__ == '__main__':
    
    app = RSSDigest()

    if len(argv) == 1:
        launch_cli_ui(app)
    elif argv[1] == 'run':
        try:
            run_profile(app, argv[2])
        except IndexError:
            print('Please specify profile name to run.')
    elif argv[1] == 'dryrun':
        try:
            dryrun_profile(app, argv[2])
        except IndexError:
            print('Please specify profile name to run.')
    else:
        print('Command not supported.')
