import configparser
import email.utils
import logging
import smtplib
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader
from rss_digest.config import AppConfig, ProfileConfig
from rss_digest.models import Context
from rss_digest.profile import Profile

class OutputError(Exception):
    """Base class for output-based exceptions."""
    pass

class BadConfigurationException(OutputError):
    """The specified output method has not been configured properly."""
    pass

class BadMethodError(OutputError):
    """The specified output method is not recognised or supported."""
    pass

class OutputGenerator:
    """A class for generating output from jinja2 templates."""

    def __init__(self, app_config: AppConfig):
        logging.info('Initialising OutputGenerator.')
        self._jinja_env = Environment(loader=FileSystemLoader(app_config.templates_dir))

    def generate(self, template: str, context: Context) -> str:
        return self._jinja_env.get_template(template).render(context=context)

class OutputSender:

    def __init__(self, app_config: AppConfig):
        self._app_config = app_config

    def send_smtp(self, output: str, profile_config: ProfileConfig):
        """Send output to an email address via SMTP."""

        try:
            username = profile_config.get_output_config_value('smtp', 'username')
            password = profile_config.get_output_config_value('smtp', 'password')
            from_email = profile_config.get_output_config_value('smtp', 'from_email')
            from_name = profile_config.get_output_config_value('smtp', 'from_name')
            to_email = profile_config.get_output_config_value('smtp', 'to_email')
            to_name = profile_config.get_output_config_value('smtp', 'to_name')
            server = profile_config.get_output_config_value('smtp', 'server')
            port = profile_config.get_output_config_value('smtp', 'port')
        except configparser.Error:
            raise BadConfigurationException('Could not read one or more necessary configuration values for SMTP. '
                                            'Check your output.ini.')

        name = profile_config.get_main_config_value('name') or profile_config.profile_name

        # Create the message
        msg = MIMEText(output, 'text')
        msg['To'] = email.utils.formataddr(to_email)
        msg['From'] = email.utils.formataddr(from_email)
        msg['Subject'] = f'{name}, your RSS digest email'

        logging.info(f'Attempting to send email to {to_email}.')

        # Connect
        server = smtplib.SMTP(server, port)
        server.ehlo()
        server.starttls()
        server.login(username, password)

        # server.set_debuglevel(True) # show communication with the server
        try:
            server.sendmail(from_email, [to_email], msg.as_string())
            logging.info('Email sent.')
        finally:
            server.quit()

    def send_stdout(self, output: str):
        """Print output to standard output."""
        print(output)

    def send_file(self, output: str, profile_config: ProfileConfig):
        """Write output to a file."""
        fpath = profile_config.get_output_config_value('file', 'path')
        with open(fpath, 'w') as f:
            f.write(output)

    def send(self, output: str, profile_config: ProfileConfig):
        """Send output using the method specified in the profile config."""
        method = profile_config.get_main_config_value('output_method')
        if method == 'smtp':
            return self.send_smtp(output, profile_config)
        elif method == 'file':
            return self.send_file(output, profile_config)
        elif method == 'stdout':
            return self.send_stdout(output)
        else:
            raise BadMethodError(f"Bad output method: \"{method}\"")