#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import smtplib
import email.utils
from email.mime.text import MIMEText

class EmailHandler:
    
    def __init__(self, profile):
        # NOTE:  By loading config in at init stage, we have to initiate
        # a separate instance for each config.  Would it be more
        # efficient to have one instance be able to handle multiple
        # configs?  Does it matter?
        self.profile = profile
        self.config = profile.config
        self.config.load_email_data()
    
    def set_email_data(self, author_name, from_addr, smtp_serv,
            smtp_port, uname, passwd):
        data = {
            'author': author_name,
            'email': from_addr,
            'smtp_server': smtp_serv,
            'smtp_port': smtp_port,
            'username': uname,
            'password': passwd
            }
        self.config.save_email_data(data)
    
    def send_email(self, msg):
        
        email_data = self.config.email_data
        
        # Create the message
        msg = MIMEText(msg, 'html')
        to_addr = (self.profile.name, self.config.get('email'))
        msg['To'] = email.utils.formataddr(to_addr)
        from_addr = (email_data['author'], email_data['email'])
        msg['From'] = email.utils.formataddr(from_addr)
        subj_str = '{}, your RSS digest email'.format(self.profile.name)
        msg['Subject'] = subj_str
        
        # Connect
        server = smtplib.SMTP(email_data['smtp_server'],
                        email_data['smtp_port'])
        server.ehlo()
        server.starttls()
        server.login(email_data['username'], email_data['password'])
        
        #server.set_debuglevel(True) # show communication with the server

        # Send email
        print(email_data['email'])
        print(self.config.get('email'))
        try:
            server.sendmail(email_data['email'],
                [self.config.get('email')], msg.as_string())
        finally:
            server.quit()
                
def main():
    from sys import argv
    if argv[1] == 'set':
        from config import Config
        c = Config(argv[2])
        eh = EmailHandler(c)
        eh.set_email_data(*argv[3:])
        print('Email data set.')

if __name__ == '__main__':
    main()
