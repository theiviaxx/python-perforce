"""Errors"""

class Error(Exception):
    pass


class CommandError(Exception):
    pass


class ChangelistError(Exception):
    pass


class ShelveError(Exception):
    pass


class RevisionError(Exception):
    pass