"""Perforce Revision Object"""
import datetime


class HeadRevision(object):
    """The HeadRevision represents the latest version on the Perforce server"""
    def __init__(self, filedict):
        self._p4dict = filedict

    @property
    def action(self):
        return self._p4dict['headAction']

    @property
    def change(self):
        return int(self._p4dict['headChange']) if self._p4dict['headChange'] else 0
    
    @property
    def revision(self):
        return int(self._p4dict['headRev'])
    
    @property
    def type(self):
        return self._p4dict['headType']
    
    @property
    def characterSet(self):
        return self._p4dict['headCharSet']
    
    @property
    def time(self):
        return datetime.datetime.fromtimestamp(int(self._p4dict['headTime']))

    @property
    def modifiedTime(self):
        return datetime.datetime.fromtimestamp(int(self._p4dict['headModTime']))