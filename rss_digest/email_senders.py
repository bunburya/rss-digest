#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import logging
import os
import smtplib
import email.utils
from email.mime.text import MIMEText

from rss_digest.config import Config
from rss_digest.profile import Profile


class EmailSender: pass


class BasicEmailSender(EmailSender):
    """A basic email sender, which sends email via an SMTP server."""

    def __init__(self, config: Config):
        self.config = config
        self.email_data_file = os.path.join(config.config_dir, 'email.json')

    def set_email_data(self, author_name: str, from_addr: str, smtp_serv: str, smtp_port: int, uname: str, passwd: str):
        data = {
            'author': author_name,
            'email': from_addr,
            'smtp_server': smtp_serv,
            'smtp_port': smtp_port,
            'username': uname,
            'password': passwd
        }
        with open(self.email_data_file, 'w') as f:
            json.dump(data, f)

    def load_email_data(self) -> dict:
        with open(self.email_data_file) as f:
            return json.load(f)

    def send_email(self, profile: Profile, msg: str):

        email_data = self.load_email_data()

        # Create the message
        msg = MIMEText(msg, 'html')
        to_addr = (profile.user_name or profile.profile_name, profile.get_conf('email'))
        msg['To'] = email.utils.formataddr(to_addr)
        from_addr = (email_data['author'], email_data['email'])
        msg['From'] = email.utils.formataddr(from_addr)
        subj_str = '{}, your RSS digest email'.format(profile.user_name or profile.profile_name)
        msg['Subject'] = subj_str

        logging.info('Attempting to send email to %s.', to_addr)

        # Connect
        server = smtplib.SMTP(email_data['smtp_server'],
                              email_data['smtp_port'])
        server.ehlo()
        server.starttls()
        server.login(email_data['username'], email_data['password'])

        # server.set_debuglevel(True) # show communication with the server

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
        server = smtplib.SMTP(email_data['smtp_server'], email_data['smtp_port'])
        server.ehlo()
        server.starttls()
        server.login(email_data['username'], email_data['password'])

        server.set_debuglevel(True)  # show communication with the server

        try:
            server.sendmail(email_data['email'], [profile.get_conf('email')], msg.as_string())
            logging.info('Test email sent.')
        finally:

            server.quit()


if __name__ == '__main__':
    main()
