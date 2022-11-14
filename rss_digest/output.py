import configparser
import email.utils
import logging
import smtplib
from abc import ABC
from datetime import datetime
from email.mime.text import MIMEText
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from rss_digest.config import Config
from rss_digest.exceptions import BadConfigurationError
from rss_digest.output_context import Context
from rss_digest.profile import Profile

logger = logging.getLogger(__name__)


class OutputGenerator:
    """A class for generating output from jinja2 templates."""

    def __init__(self, app_config: Config):
        logger.info('Initialising OutputGenerator.')
        self._jinja_env = Environment(loader=FileSystemLoader(app_config.templates_dir))

    def generate(self, template: str, context: Context) -> str:
        return self._jinja_env.get_template(template).render(ctx=context)


class BaseOutputSender(ABC):
    """A base class for sending a generated digest to a user in some way."""

    def __init__(self, app_config: Config):
        self.app_config = app_config

    def send(self, output: str, profile: Profile):
        raise NotImplementedError

class SendmailOutputSender(BaseOutputSender):
    """Output digest in a format readable by `sendmail -t`."""

    def send(self, output: str, profile: Profile):
        email_addr = profile.config['email']
        name = profile.config.get('name') or profile.name
        date_fmt = profile.config['date_format']
        date = datetime.today().strftime(date_fmt)
        print(f'To: {email_addr}')
        print(f'Subject: {name}, your RSS digest for {date}')
        print(output)

# class OutputSender:
#
#     def __init__(self, app_config: Config):
#         self._app_config = app_config
#
#     def send_smtp(self, output: str, profile_config: ProfileConfig):
#         """Send output to an email address via SMTP."""
#
#         try:
#             username = profile_config.get_output_config_value('smtp', 'username')
#             password = profile_config.get_output_config_value('smtp', 'password')
#             from_email = profile_config.get_output_config_value('smtp', 'from_email')
#             from_name = profile_config.get_output_config_value('smtp', 'from_name')
#             to_email = profile_config.get_output_config_value('smtp', 'to_email')
#             to_name = profile_config.get_output_config_value('smtp', 'to_name')
#             server = profile_config.get_output_config_value('smtp', 'server')
#             port = profile_config.get_output_config_value('smtp', 'port')
#         except configparser.Error:
#             raise BadConfigurationError('Could not read one or more necessary configuration values for SMTP. '
#                                         'Check your output.ini.')
#
#         name = profile_config.get_main_config_value('name') or profile_config.profile_name
#
#         # Create the message
#         msg = MIMEText(output, 'text')
#         msg['To'] = email.utils.formataddr(to_email)
#         msg['From'] = email.utils.formataddr(from_email)
#         msg['Subject'] = f'{name}, your RSS digest email'
#
#         logger.info(f'Attempting to send email to {to_email}.')
#
#         # Connect
#         server = smtplib.SMTP(server, port)
#         server.ehlo()
#         server.starttls()
#         server.login(username, password)
#
#         # server.set_debuglevel(True) # show communication with the server
#         try:
#             server.sendmail(from_email, [to_email], msg.as_string())
#             logger.info('Email sent.')
#         finally:
#             server.quit()
#
#     def send_stdout(self, output: str):
#         """Print output to standard output."""
#         print(output)
#
#     def send_file(self, output: str, profile_config: ProfileConfig):
#         """Write output to a file."""
#         fpath = profile_config.get_output_config_value('file', 'path')
#         with open(fpath, 'w') as f:
#             f.write(output)
#
#     def send(self, output: str, profile_config: ProfileConfig, method: Optional[str] = None):
#         """Send output using the method specified in the profile config."""
#         method = method or profile_config.get_main_config_value('output_method')
#         if method == 'smtp':
#             return self.send_smtp(output, profile_config)
#         elif method == 'file':
#             return self.send_file(output, profile_config)
#         elif method == 'stdout':
#             return self.send_stdout(output)
#         else:
#             raise BadConfigurationError(f"Bad output method: \"{method}\"")
