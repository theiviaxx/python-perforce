"""Perforce Revision Object"""

import logging

import path

from perforce import errors
from perforce import headrevision

LOGGER = logging.getLogger(__name__)


class Revision(object):
    """A Revision represents a file on perforce at a given point in it's history"""
    def __init__(self, data, connection):
        self._p4dict = data
        self._connection = connection
        self._head = headrevision.HeadRevision(self._p4dict)
        self._changelist = None

    def __len__(self):
        if 'fileSize' not in self._p4dict:
            self._p4dict = self._connection.run('fstat -m 1 -Ol %s' % self.depotFile[0])[0]
        
        return int(self._p4dict['fileSize'])

    def __str__(self):
        return self.depotFile

    def __repr__(self):
        return '<%s: %s#%s>' % (self.__class__.__name__, self.depotFile, self.revision)

    def __int__(self):
        return self.revision

    def query(self):
        """Runs an fstat for this file and repopulates the data"""
        
        self._p4dict = self._connection.run('fstat -m 1 %s' % self._p4dict['depotFile'])[0]
        self._head = headrevision.HeadRevision(self._p4dict)

        self._filename = self.depotFile

    def edit(self, changelist=0):
        """Checks out the file

        :param changelist: Optional changelist to checkout the file into
        :type changelist: Changelist
        """
        if changelist:
            self._connection.run('edit -c %i %s' % (int(changelist), self.depotFile))
        else:
            self._connection.run('edit %s' % self.depotFile)

        self.query()

    def lock(self, lock=True, changelist=0):
        """Locks or unlocks the file

        :param lock: Lock or unlock the file
        :type lock: bool
        :param changelist: Optional changelist to checkout the file into
        :type changelist: Changelist
        """

        cmd = 'lock' if lock else 'unlock'
        if changelist:
            self._connection.run('%s -c %i %s' % (cmd, changelist, self.depotFile))
        else:
            self._connection.run('%s %s' % (cmd, self.depotFile))

        self.query()

    def sync(self, force=False, safe=True, revision=0):
        """Syncs the file at the current revision

        :param force: Force the file to sync
        :type force: bool
        :param safe: Don't sync files that were changed outside perforce
        :type safe: bool
        :param revision: Sync to a specific revision
        :type revision: int
        """
        args = ''
        if force:
            args += ' -f'

        if safe:
            args += ' -s'

        args += ' %s' % self.depotFile
        if revision:
            args += '#{}'.format(revision)
        self._connection.run('sync %s' % args)

        self.query()

    def revert(self, unchanged=False):
        """Reverts any file changes

        :param unchanged: Only revert if the file is unchanged
        :type unchanged: bool
        """
        args = ''
        if unchanged:
            args += ' -a'

        wasadd = self.action == 'add'

        args += ' %s' % self.depotFile
        self._connection.run('revert %s' % args)

        if not wasadd:
            self.query()

        if self._changelist:
            self._changelist.remove(self, permanent=True)

    def shelve(self, changelist=None):
        """Shelves the file if it is in a changelist"""
        if changelist is None and self.changelist.description == 'default':
            raise errors.ShelveError('Unabled to shelve files in the default changelist')

        cmd = 'shelve '
        if changelist:
            cmd += '-c {0} '.format(int(changelist))
        
        cmd += self.depotFile

        self._connection.run(cmd)

        self.query()

    def move(self, dest, changelist=0, force=False):
        """Renames/moves the file to dest"""
        args = ''
        if force:
            args += '-f'

        if changelist:
            args += ' -c {} '.format(changelist)

        if not self.isEdit:
            self.edit(changelist)

        args += '{0} {1}'.format(self.depotFile, dest)
        LOGGER.info('move {}'.format(args))
        self._connection.run('move {}'.format(args))

        self.query()

    def delete(self, changelist=0):
        """Marks the file for delete"""
        args = ''

        if changelist:
            args += ' -c %i' % changelist

        args += ' %s' % self.depotFile
        self._connection.run('delete %s' % args)

        self.query()

    @property
    def hash(self):
        """The hash value of the current revision"""
        if 'digest' not in self._p4dict:
            self._p4dict = self._connection.run('fstat -m 1 -Ol %s' % self.depotFile)[0]
        
        return self._p4dict['digest']

    @property
    def clientFile(self):
        """The local path to the revision"""
        return path.path(self._p4dict['clientFile'])

    @property
    def depotFile(self):
        """The depot path to the revision"""
        return path.path(self._p4dict['depotFile'])

    @property
    def movedFile(self):
        """Was this file moved"""
        return self._p4dict['movedFile']

    @property
    def isMapped(self):
        """Is the fiel mapped to the current workspace"""
        return 'isMapped' in self._p4dict

    @property
    def isShelved(self):
        """Is the file shelved"""
        return 'shelved' in self._p4dict
    
    @property
    def revision(self):
        """Revision number"""
        rev = self._p4dict.get('haveRev', -1)
        if rev == 'none':
            rev = 0
        return int(rev)

    @property
    def description(self):
        return self._p4dict.get('desc')
    
    @property
    def action(self):
        """The current action: add, edit, etc."""
        return self._p4dict.get('action')

    @property
    def changelist(self):
        """Which changelist is this revision in"""
        import changelist
        if self._changelist:
            return self._changelist

        if self._p4dict['change'] == 'default':
            return self._connection.default
        else:
            return changelist.Changelist(self._connection, int(self._p4dict['change']))

    @changelist.setter
    def changelist(self, value):
        import changelist
        if not isinstance(value, changelist.Changelist):
            raise TypeError('argument needs to be an instance of Changelist')

        self._changelist = value
    
    @property
    def type(self):
        """Best guess at file type. text or binary"""
        if self.action == 'edit':
            return self._p4dict['type']

        return None

    @property
    def isResolved(self):
        """Is the revision resolved"""
        return self.unresolved == 0
    
    @property
    def resolved(self):
        """Is the revision resolved"""
        return int(self._p4dict.get('resolved', 0))
    
    @property
    def unresolved(self):
        """Is the revision unresolved"""
        return int(self._p4dict.get('unresolved', 0))
    
    @property
    def openedBy(self):
        """Who has this file open for edit"""
        return self._p4dict.get('otherOpen', [])
    
    @property
    def lockedBy(self):
        """Who has this file locked"""
        return self._p4dict.get('otherLock', [])

    @property
    def isLocked(self):
        """Is the file locked by anyone excluding the current user"""
        return 'ourLock' in self._p4dict or 'otherLock' in self._p4dict
    
    @property
    def head(self):
        """The :py:class:HeadRevision of this file"""
        return self._head

    @property
    def isSynced(self):
        """Is the local file the latest revision"""
        return self.revision == self.head.revision

    @property
    def isEdit(self):
        return self.action == 'edit'
    
    

