import logging

from os.path import exists

class CLInterface:
    """A very simple CLI for adding profiles and feeds."""
    
    def __init__(self, app):
        self.app = app
        print('Welcome to RSS Digest.')
        if not exists(self.app.config.email_data_file):
            print('No email.json file found.  Add details of how RSS Digest is to send emails.')
            self.set_email_data()
        self.repl()
       
    def force_input(self, prompt=None, msg=None, cmd=input):
        response = False
        while not response:
            response = cmd(prompt)
            if (not response) and msg:
                print(msg)
        return response
       
    def set_email_data(self):
        data = {}
        author = input('Who should emails from RSS Digest appear as coming from '
                        '(default is "RSSDigest")? ') or 'RSSDigest'
        email = self.force_input('Email address from which emails are sent:',
                            'An email address is required. ')
        smtp_server = self.force_input('SMTP server: ',
                            'An SMTP server is required.')
        smtp_port = input('SMTP port (default is 587): ') or 587
        username = input('Email username (default is the email address): ') or email
        password = self.force_input('Email password (this is stored as plaintext): ',
                                'Your password is required.', getpass)
        data = {
            'author': author,
            'email': email,
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'username': username,
            'password': password
            }
        self.app.config.save_email_data(data)
        
    def add_feed(self, profile=None):
        if profile is None:
            profile = input('Which profile? ').strip()
            if profile not in self.app.profiles:
                print('Invalid profile.  Enter existing profile name or create new profile.')
                return
        p = self.app.get_profile(profile)
        save_and_quit = False
        while not save_and_quit:
            title = input('Enter feed title: ')
            url = input('Enter feed URL: ')
            category = input('Enter category (blank for no category): ') or None
            p.add_feed(title, url, posn=-1, save=False, category=category)
            again = input('Add another? (y/N) ')
            if not again.lower().startswith('y'):
                save_and_quit = True
            p.save_data()
            p.save_list()
    
    def remove_profile(self):
        name = self.force_input('Enter name of profile to remove: ',
                                'You need to enter a profile name.')
        try:
            self.app.del_profile(name)
            print('Removed profile {}.'.format(name))
        except FileNotFoundError:
            print('No profile {} to delete.'.format(name))

    def add_profile(self):
        name = email = None
        while not (name and email):
            name = input('Enter profile name: ')
            email = input('Enter email address: ')
            if not (name and email):
                print('You need to enter both a name and an email.')
        profile = self.app.new_profile(name, email)
        print('Profile {} added.  Now add some feeds.'.format(name))
        self.add_feed(profile.name)
    
    def email_profile(self):
        name = self.force_input('Enter profile name: ',
                                'You need to enter a profile name.')
        try:
            self.app.email_profile_name(name)
            print('Email sent for profile {}.'.format(name))
        except ValueError:
            print('Profile {} not found.'.format(name))
    
    def print_profile_output_to_file(self):
        # Print output to a specific file - the default is just for
        # testing purposes.  Later, remove this or set a sensible default.
        default_outfile = 'output.html'
        name = self.force_input('Enter profile name: ',
                                'You need to enter a profile name.')
        outfile = input('Enter output file (default is $PWD/outfile.html):') or default_outfile
        profile = self.app.get_profile(name)
        html = self.app.get_output_for_profile(profile)
        with open(outfile, 'w') as f:
            f.write(html)
        logging.info('Output for profile %s written to file %s.', name,
                        outfile)
        #profile.update_last_updated()
        #profile.feed_handler.save()
    
    def test_email(self):
        name = self.force_input('Enter profile name: ',
                                'You need to enter a profile name.')
        profile = self.app.get_profile(name)
        self.app.email_handler.test_email(profile)
    
    def print_cmds(self):
        print('Commands (none of these take arguments; you will be prompted for input after entering the commands):')
        print('add_profile:  Add a new profile.')
        print('add_feed:  Add a feed to a profile.')
        print('del_profile:  Delete a profile.')
        print('email_profile:  Send an RSS digest email for a specific profile.')
        print('test_email:  Send a test email to a specific profile.')
        print('print_file:  Print the output for a specific profile to a file.')
        print('exit:  Exit the app.')
        
    def eval_cmd(self):        
        try:
            cmd = input('Enter command: ').lower().split()[0]
        except IndexError:
            # empty input; do nothing
            return
        if cmd == 'add_profile':
            self.add_profile()
        elif cmd == 'add_feed':
            self.add_feed()
        elif cmd == 'del_profile':
            self.remove_profile()
        elif cmd == 'email_profile':
            self.email_profile()
        elif cmd == 'test_email':
            self.test_email()
        elif cmd == 'print_file':
            self.print_profile_output_to_file()
        elif cmd == 'exit':
            raise SystemExit
        else:
            print('Sorry, command {} not recognised.'.format(cmd))
    
    def repl(self):
        self.print_cmds()
        while True:
            self.eval_cmd()
