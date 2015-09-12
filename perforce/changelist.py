"""Perforce Changelist Object"""

import logging
import subprocess
import datetime
import traceback

from perforce import revision
from perforce import errors


LOGGER = logging.getLogger('Perforce')
LOGGER.setLevel(logging.DEBUG)
FORMAT = """Change: {change}

Client: {client}

User:   {user}

Status: {status}

Description:
    {description}

Files:
{files}
"""

NEW_FORMAT = """Change: new

Client: {client}

Status: new

Description:
    {description}

"""


def create(connection):
    """Creates a new changelist"""
    form = NEW_FORMAT.format(client=connection._client, description='<Created by Python>')
    result = connection.run('change -i', form, marshal_output=False)

    return Changelist(connection, int(result.split()[1]))


class Changelist(object):
    """A Changelist is a collection of files that will be submitted as a single entry with a description and timestamp"""
    def __init__(self, connection, changelist=None):
        super(Changelist, self).__init__()

        self._connection = connection
        self._files = []
        self._dirty = False
        self._reverted = False

        self._change = changelist
        self._description = ''
        self._client = ''
        self._time = datetime.datetime.now()
        self._status = 'pending'
        self._user = ''

        if self._change:
            data = self._connection.run('describe {0}'.format(changelist))[0]
            self._description = data['desc']
            self._client = data['client']
            self._time = datetime.datetime.fromtimestamp(int(data['time']))
            self._status = data['status']
            self._user = data['user']

            for k, v in data.iteritems():
                if k.startswith('depotFile'):
                    self.append(v)

    def __repr__(self):
        return '<Changelist {}>'.format(self._change)

    def __int__(self):
        return int(self._change)

    def __nonzero__(self):
        return True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type:
            LOGGER.debug(traceback.format_exc())
            raise errors.ChangelistError(exc_value)

        self.save()

    def __contains__(self, other):
        if not isinstance(other, revision.Revision):
            raise TypeError('Value needs to be a Revision instance')

        names = [f.depotFile for f in self._files]

        return other.depotFile in names

    def __getitem__(self, name):
        return self._files[name]

    def __len__(self):
        return len(self._files)

    def __del__(self):
        """Reverts all files in this changelist then deletes the changelist from perforce"""
        try:
            self.revert()
        except errors.ChangelistError:
            pass

        self._connection.run('change -d {0}'.format(self._change))

    def query(self):
        """Queries the depot to get the current status of the changelist"""
        self._files = []
        data = self._connection.run('describe {0}'.format(self._change))[0]
        self._description = data['desc']
        self._client = data['client']
        self._time = datetime.datetime.fromtimestamp(int(data['time']))
        self._status = data['status']
        self._user = data['user']

        for k, v in data.iteritems():
            if k.startswith('depotFile'):
                self.append(v)

    def append(self, rev):
        """Adds a :py:class:Revision to this changelist and adds or checks it out if needed

        :param rev: Revision to add
        :type rev: :class:`.Revision`
        """
        if not isinstance(rev, revision.Revision):
            results = self._connection.ls(rev)
            if not results:
                self._connection.add(rev, self)
                return
            
            rev = results[0]

        if not rev in self:
            if rev.isMapped:
                rev.edit(self)
            else:
                return

            self._files.append(rev)
            rev.changelist = self

            self._dirty = True

    def remove(self, rev, permanent=False):
        """Removes a revision from this changelist

        :param rev: Revision to remove
        :type rev: :class:`.Revision`
        :param permanent: Whether or not we need to set the changelist to default
        :type permanent: bool
        """
        if not isinstance(rev, revision.Revision):
            raise TypeError('argument needs to be an instance of Revision')

        if rev not in self:
            raise ValueError('{} not in changelist'.format(rev))

        self._files.remove(rev)
        if not permanent:
            rev.changelist = self._connection.default

    def revert(self):
        """Revert all files in this changelist

        :raises: :class:`.ChangelistError`
        """
        if self._reverted:
            raise errors.ChangelistError('This changelist has been reverted')

        change = self._change
        if self._change == 0:
            change = 'default'
        
        filelist = [str(f) for f in self]
        self._connection.run('revert -c {0} {1}'.format(change, ' '.join(filelist)))

        self._files = []
        self._reverted = True

    def save(self):
        """Saves the state of the changelist"""
        form = FORMAT.format(
            change=self._change,
            client=self._client,
            #time=self._time,
            user=self._user,
            status=self._status,
            description=self._description,
            files='\n'.join(['    {0}'.format(f.depotFile) for f in self._files])
        )
        
        self._connection.run('change -i', stdin=form, marshal_output=False)
        self._dirty = False

    def submit(self):
        """Submits a chagelist to the depot"""
        if self._dirty:
            self.save()

        self._connection.run('submit -c {}'.format(int(self)), marshal_output=False)

    @property
    def change(self):
        """Changelist number"""
        return self._change

    @property
    def client(self):
        """Perforce client this changelist is under"""
        return self._client

    @client.setter
    def client(self, client):
        self._client = client
        self._dirty = True

    @property
    def description(self):
        """Changelist description"""
        return self._description.strip()

    @description.setter
    def description(self, desc):
        self._description = desc
        self._dirty = True
    
    @property
    def isDirty(self):
        """Does this changelist have unsaved changes"""
        return self._dirty

    @property
    def time(self):
        """Creation time of this changelist"""
        return self._time

    @property
    def status(self):
        """Status of this changelist.  Pending, Submitted, etc."""
        return self._status

    @property
    def user(self):
        """User who created this changelist"""
        return self._user


class Default(Changelist):
    def __init__(self, connection):
        super(Default, self).__init__(connection, None)
        
        data = self._connection.run('opened -c default')
        
        for f in data:
            self._files.append(revision.Revision(f['depotFile'], f))

        data = self._connection.run('change -o')[0]
        data = self._connection.run('change -o')[0]
        self._change = 0
        self._description = self._connection.run('change -o')[0]['Description']
        self._client = connection.client
        self._time = None
        self._status = 'new'
        self._user = connection.user

    def save(self):
        """Saves the state of the changelist"""
        files = ','.join([f.depotFile for f in self._files])
        self._connection.run('reopen -c default {}'.format(files))
        self._dirty = False
