import logging
from typing import Optional

from rss_digest.cli import CLI, get_arg_parser

logger = logging.getLogger(__name__)
def main() -> Optional[int]:
    _cli = CLI()
    parser = get_arg_parser(_cli)
    ns = parser.parse_args()
    _cli.configure(ns)
    try:
        ns.func(ns)
    except AttributeError:
        # Script probably called without specifying command. Print help and exit (with error status)
        parser.print_help()
        return 1
    except KeyboardInterrupt as e:
        # Log keyboard interrupt and exit silently
        logger.exception(e)
        return 1
    except BaseException as e:
        # Some other error was encountered - log it and report to user.
        logger.exception(e)
        print('Encountered one or more uncaught exceptions. Check logs for details.')
        return 1
