#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import smtplib
import email.utils
from email.mime.text import MIMEText

class EmailHandler:
    
    def __init__(self, app):
        self.config = app.config
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
    
    def send_email(self, profile, msg):
                
        email_data = self.config.email_data
        
        # Create the message
        msg = MIMEText(msg, 'html')
        to_addr = (profile.name, profile.get_conf('email'))
        msg['To'] = email.utils.formataddr(to_addr)
        from_addr = (email_data['author'], email_data['email'])
        msg['From'] = email.utils.formataddr(from_addr)
        subj_str = '{}, your RSS digest email'.format(profile.name)
        msg['Subject'] = subj_str
        
        logging.info('Attempting to send email to %s.', to_addr)
        
        # Connect
        server = smtplib.SMTP(email_data['smtp_server'],
                        email_data['smtp_port'])
        server.ehlo()
        server.starttls()
        server.login(email_data['username'], email_data['password'])
        
        #server.set_debuglevel(True) # show communication with the server

        try:
            server.sendmail(email_data['email'],
                [profile.get_conf('email')], msg.as_string())
            logging.info('Email sent.')
        finally:
            
            server.quit()
    
    def test_email(self, profile):
        email_data = self.config.email_data
        
        # Create the message
        msg = MIMEText('This is a test email.', 'html')
        to_addr = (profile.name, profile.get_conf('email'))
        msg['To'] = email.utils.formataddr(to_addr)
        from_addr = (email_data['author'], email_data['email'])
        msg['From'] = email.utils.formataddr(from_addr)
        subj_str = 'Test email'.format(profile.name)
        msg['Subject'] = subj_str
        
        logging.info('Attempting to send test email to %s.', to_addr)
        
        # Connect
        server = smtplib.SMTP(email_data['smtp_server'],
                        email_data['smtp_port'])
        server.ehlo()
        server.starttls()
        server.login(email_data['username'], email_data['password'])
        
        server.set_debuglevel(True) # show communication with the server

        try:
            server.sendmail(email_data['email'],
                [profile.get_conf('email')], msg.as_string())
            logging.info('Test email sent.')
        finally:
            
            server.quit()
    
if __name__ == '__main__':
    main()
