"""Errors"""

class Error(Exception):
    pass


class CommandError(Exception):
    """Errors that occur while running a command"""


class ChangelistError(Exception):
    """Errors that occur in a Changelist"""


class ShelveError(Exception):
    """Errors that occur when shelving/unshelving a file revision"""


class RevisionError(Exception):
    """Errors that occur on a file revision"""


class ConnectionError(Exception):
    """Errors that occured with the connection"""
