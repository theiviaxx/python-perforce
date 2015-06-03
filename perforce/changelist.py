"""Perforce Changelist Object"""

import subprocess
import datetime

from perforce import revision
from perforce import errors


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
    form = NEW_FORMAT.format(client=connection._client, description='<Created by Python>')
    result = connection.run('change -i', form, marshal_output=False)

    return Changelist(connection, int(result.split()[1]))


class Changelist(object):
    def __init__(self, connection, changelist=None):
        super(Changelist, self).__init__()

        self._connection = connection
        self._files = []
        self._dirty = False

        self._change = changelist
        self._description = ''
        self._client = ''
        self._time = datetime.datetime.now()
        self._status = 'pending'
        self._user = ''

        if self._change:
            data = self._connection.run('describe {0}'.format(changelist))[0]
            self._change = changelist
            self._description = data['desc']
            self._client = data['client']
            self._time = datetime.datetime.fromtimestamp(int(data['time']))
            self._status = data['status']
            self._user = data['user']

            for k, v in data.iteritems():
                if k.startswith('depotFile'):
                    self.append(v)

    def __int__(self):
        return int(self._change)

    def __enter__(self):
        return self

    def __exit__(self, exctype, excvalue, traceback):
        if exctype:
            raise errors.ChangelistError(excvalue)

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
        self._connection.run('change -d {0}'.format(self._change))

    def query(self):
        """Queries the depot to get the current status of the changelist"""
        data = self._connection.run('describe {0}'.format(self._change))[0]
        self._description = data['desc']
        self._client = data['client']
        self._time = datetime.datetime.fromtimestamp(int(data['time']))
        self._status = data['status']
        self._user = data['user']

        for k, v in data.iteritems():
            if k.startswith('depotFile'):
                self.append(v)

    def append(self, item):
        if not isinstance(item, revision.Revision):
            item = self._connection.ls(item)[0]

        if not item in self:
            if not item.isMapped and item.action != 'add':
                item.add()
            elif item.isMapped and item.action != 'edit':
                item.edit()

            self._files.append(item)

            self._dirty = True

    @property
    def change(self):
        return self._change

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, client):
        self._client = client
        self._dirty = True

    @property
    def description(self):
        return self._description.strip()

    @description.setter
    def description(self, desc):
        self._description = desc
        self._dirty = True
    
    @property
    def isDirty(self):
        return self._dirty

    @property
    def time(self):
        return self._time

    @property
    def status(self):
        return self._status

    @property
    def user(self):
        return self._user

    # def revert(self):
    #     if self._reverted:
    #         raise errors.ChangelistError('This changelist has been reverted')

    #     if self._change:
    #         self._connection.run('revert -c {0} {1}'.format(self._change, ' '.join(self)))
    #         self._reverted = True
    #     else:
    #         raise errors.ChangelistError('Cannot revert the defualt changelist')

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
        self._connection.run('change -i', form, marshal_output=False)
        self._dirty = False

    def submit(self):
        """Submits a chagelist to the depot"""
        if self._dirty:
            self.save()

        self._connection.run('submit -c {}'.format(int(self)), marshal_output=False)


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
