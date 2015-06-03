"""Perforce Revision Object"""

import path

from perforce import errors
from perforce import headrevision



class Revision(object):
    def __init__(self, data, connection):
        self._p4dict = data
        self._connection = connection
        self._head = headrevision.HeadRevision(self._p4dict)

    def __len__(self):
        if 'fileSize' not in self._p4dict:
            self._p4dict = self._connection.run('fstat -m 1 -Ol %s' % self.depotFile[0])[0]
        
        return int(self._p4dict['fileSize'])

    def __repr__(self):
        return '<%s: %s#%s>' % (self.__class__.__name__, self.depotFile, self.revision)

    def __query(self):
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

        self.__query()

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

        self.__query()

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
            args += '#%i' % revision
        self._connection.run('sync %s' % args)

        self.__query()

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
            self.__query()

    def shelve(self, changelist=None):
        """Shelves the file if it is in a changelist"""
        if changelist is None and self.change.description == 'default':
            raise errors.ShelveError('Unabled to shelve files in the default changelist')

        cmd = 'shelve '
        if changelist:
            cmd += '-c {0} '.format(int(changelist))
        
        cmd += self.depotFile

        self._connection.run(cmd)

        self.__query()

    def move(self, dest, changelist=0, force=False):
        """Renames/moves the file to dest"""
        args = ''
        if force:
            args += ' -f'

        if changelist:
            args += ' -c %i' % changelist

        args += ' %s %s' % (self.depotFile, dest)
        self._connection.run('move %s' % args)

        self.__query()

    def delete(self, changelist=0):
        """Marks the file for delete"""
        args = ''

        if changelist:
            args += ' -c %i' % changelist

        args += ' %s' % self.depotFile
        self._connection.run('delete %s' % args)

        self.__query()

    @property
    def hash(self):
        if 'digest' not in self._p4dict:
            self._p4dict = self._connection.run('fstat -m 1 -Ol %s' % self.depotFile)[0]
        
        return self._p4dict['digest']

    @property
    def clientFile(self):
        return path.path(self._p4dict['clientFile'])

    @property
    def depotFile(self):
        return path.path(self._p4dict['depotFile'])

    @property
    def movedFile(self):
        return self._p4dict['movedFile']

    @property
    def isMapped(self):
        return 'isMapped' in self._p4dict

    @property
    def isShelved(self):
        return 'shelved' in self._p4dict
    
    @property
    def revision(self):
        rev = self._p4dict.get('haveRev', -1)
        if rev == 'none':
            rev = 0
        return int(rev)

    @property
    def description(self):
        return self._p4dict.get('desc')
    
    @property
    def action(self):
        return self._p4dict.get('action')

    @property
    def change(self):
        import changelist
        if self._p4dict['change'] == 'default':
            return changelist.Default(self._connection)
        else:
            return changelist.Changelist(self._connection, int(self._p4dict['change']))
    
    @property
    def type(self):
        if self.action == 'edit':
            return self._p4dict['type']

        return None
    
    @property
    def characterSet(self):
        return self._p4dict['charSet']

    @property
    def isResolved(self):
        return self.unresolved == 0
    
    @property
    def resolved(self):
        return int(self._p4dict.get('resolved', 0))
    
    @property
    def unresolved(self):
        return int(self._p4dict.get('unresolved', 0))
    
    @property
    def openedBy(self):
        return self._p4dict.get('otherOpen', [])
    
    @property
    def lockedBy(self):
        return self._p4dict.get('otherLock', [])

    @property
    def isLocked(self):
        return 'ourLock' in self._p4dict or 'otherLock' in self._p4dict
    
    @property
    def head(self):
        return self._head

    @property
    def isSynced(self):
        return self.revision == self.head.revision

