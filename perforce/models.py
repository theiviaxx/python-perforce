# -*- coding: utf-8 -*-

"""
perforce.models
~~~~~~~~~~~~~~~

This module implements the main data models used by perforce

:copyright: (c) 2015 by Brett Dixon
:license: MIT, see LICENSE for more details
"""

import subprocess
import datetime
import traceback
import os
import marshal
import logging
import re
from collections import namedtuple
from functools import wraps

import path
import six

from perforce import errors


LOGGER = logging.getLogger(__name__)
CHAR_LIMIT = 8000
DATE_FORMAT = "%Y/%m/%d %H:%M:%S"
FORMAT = """Change: {change}

Client: {client}

User:   {user}

Status: {status}

Description:
\t{description}

Files:
{files}
"""

NEW_FORMAT = """Change: new

Client: {client}

Status: new

Description:
\t{description}

"""


#: Error levels enum
ErrorLevel = namedtuple('ErrorLevel', 'EMPTY, INFO, WARN, FAILED, FATAL')(*range(5))
#: Connections status enum
ConnectionStatus = namedtuple('ConnectionStatus', 'OK, OFFLINE, NO_AUTH, INVALID_CLIENT')(*range(4))
#: File spec http://www.perforce.com/perforce/doc.current/manuals/cmdref/filespecs.html
FileSpec = namedtuple('FileSpec', 'depot,client')

RE_FILESPEC = re.compile('^"?(//[\w\d\_\/\.\s]+)"?\s')


def split_ls(func):
    """Decorator to split files into manageable chunks as not to exceed the windows cmd limit

    :param func: Function to call for each chunk
    :type func: :py:class:Function
    """
    @wraps(func)
    def wrapper(self, files, silent=True, exclude_deleted=False):
        if not isinstance(files, (tuple, list)):
            files = [files]

        counter = 0
        index = 0
        results = []

        while files:
            if index >= len(files):
                results += func(self, files, silent, exclude_deleted)
                break

            length = len(str(files[index]))
            if length + counter > CHAR_LIMIT:
                # -- at our limit
                runfiles = files[:index]
                files = files[index:]
                counter = 0
                index = 0
                results += func(self, runfiles, silent, exclude_deleted)
                runfiles = None
                del runfiles
            else:
                index += 1
                counter += length

        return results

    return wrapper


def camel_case(string):
    """Makes a string camelCase

    :param string: String to convert
    """
    return ''.join((string[0].lower(), string[1:]))


class Connection(object):
    """This is the connection to perforce and does all of the communication with the perforce server"""
    def __init__(self, port=None, client=None, user=None, executable='p4', level=ErrorLevel.FAILED):
        self._executable = executable
        self._level = level

        self._port = port
        self._client = client
        self._user = user
        self.__getVariables()

        # -- Make sure we can even proceed with anything
        if self._port is None:
            raise errors.ConnectionError('Perforce host could not be found, please set P4PORT or provide the hostname\
and port')

        if self._user is None:
            raise errors.ConnectionError('No user could be found, please set P4USER or provide the user')

    def __repr__(self):
        return '<Connection: {0}, {1}, {2}>'.format(self._port, str(self._client), self._user)

    def __getVariables(self):
        """Parses the P4 env vars using 'set p4'"""
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            output = subprocess.check_output([self._executable, 'set'], startupinfo=startupinfo)
            if six.PY3:
                output = str(output, 'utf8')
        except subprocess.CalledProcessError as err:
            LOGGER.error(err)
            return

        p4vars = {}
        for line in output.splitlines():
            if not line:
                continue
            try:
                k, v = line.split('=', 1)
            except ValueError:
                continue
            p4vars[k.strip()] = v.strip().split(' (')[0]
            if p4vars[k.strip()].startswith('(config'):
                del p4vars[k.strip()]

        self._port = self._port or os.getenv('P4PORT', p4vars.get('P4PORT'))
        self._user = self._user or os.getenv('P4USER', p4vars.get('P4USER'))
        self._client = self._client or os.getenv('P4CLIENT', p4vars.get('P4CLIENT'))

    @property
    def client(self):
        """The client used in perforce queries"""
        if isinstance(self._client, six.string_types):
            self._client = Client(self._client, self)

        return self._client

    @client.setter
    def client(self, value):
        if isinstance(value, Client):
            self._client = value
        elif isinstance(value, six.string_types):
            self._client = Client(value, self)
        else:
            raise TypeError('{} not supported for client'.format(type(value)))

    @property
    def user(self):
        """The user used in perforce queries"""
        return self._user

    @property
    def level(self):
        """The current exception level"""
        return self._level

    @level.setter
    def level(self, value):
        """Set the current exception level"""
        self._level = value

    @property
    def status(self):
        """The status of the connection to perforce"""
        try:
            # -- Check client
            res = self.run(['info'])
            if res[0]['clientName'] == '*unknown*':
                return ConnectionStatus.INVALID_CLIENT
            # -- Trigger an auth error if not logged in
            self.run(['user', '-o'])
        except errors.CommandError as err:
            if 'password (P4PASSWD) invalid or unset' in str(err.args[0]):
                return ConnectionStatus.NO_AUTH
            if 'Connect to server failed' in str(err.args[0]):
                return ConnectionStatus.OFFLINE

        return ConnectionStatus.OK

    def run(self, cmd, stdin=None, marshal_output=True, **kwargs):
        """Runs a p4 command and returns a list of dictionary objects

        :param cmd: Command to run
        :type cmd: list
        :param stdin: Standard Input to send to the process
        :type stdin: str
        :param marshal_output: Whether or not to marshal the output from the command
        :type marshal_output: bool
        :param kwargs: Passes any other keyword arguments to subprocess
        :raises: :class:`.error.CommandError`
        :returns: list, records of results
        """
        records = []
        args = [self._executable, "-u", self._user, "-p", self._port]

        if self._client:
            args += ["-c", str(self._client)]

        if marshal_output:
            args.append('-G')

        if isinstance(cmd, six.string_types):
            raise ValueError('String commands are not supported, please use a list')

        args += cmd

        command = ' '.join(args)

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo,
            **kwargs
        )

        if stdin:
            proc.stdin.write(six.b(stdin))

        if marshal_output:
            try:
                while True:
                    record = marshal.load(proc.stdout)
                    if record.get(b'code', '') == b'error' and record[b'severity'] >= self._level:
                        proc.stdin.close()
                        proc.stdout.close()
                        raise errors.CommandError(record[b'data'], record, command)
                    if isinstance(record, dict):
                        if six.PY2:
                            records.append(record)
                        else:
                            records.append({str(k, 'utf8'): str(v) if isinstance(v, int) else str(v, 'utf8', errors='ignore') for k, v in record.items()})
            except EOFError:
                pass

            stdout, stderr = proc.communicate()
        else:
            records, stderr = proc.communicate()

        if stderr:
            raise errors.CommandError(stderr, command)

        return records

    @split_ls
    def ls(self, files, silent=True, exclude_deleted=False):
        """List files

        :param files: Perforce file spec
        :type files: list
        :param silent: Will not raise error for invalid files or files not under the client
        :type silent: bool
        :param exclude_deleted: Exclude deleted files from the query
        :type exclude_deleted: bool
        :raises: :class:`.errors.RevisionError`
        :returns: list<:class:`.Revision`>
        """
        try:
            cmd = ['fstat']
            if exclude_deleted:
                cmd += ['-F', '^headAction=delete ^headAction=move/delete']

            cmd += files

            results = self.run(cmd)
        except errors.CommandError as err:
            if silent:
                results = []
            elif "is not under client's root" in str(err):
                raise errors.RevisionError(err.args[0])
            else:
                raise

        return [Revision(r, self) for r in results if r.get('code') != 'error']

    def findChangelist(self, description=None):
        """Gets or creates a Changelist object with a description

        :param description: The description to set or lookup
        :type description: str
        :returns: :class:`.Changelist`
        """
        if description is None:
            change = Default(self)
        else:
            if isinstance(description, six.integer_types):
                change = Changelist(description, self)
            else:
                pending = self.run(['changes', '-l', '-s', 'pending', '-c', str(self._client), '-u', self._user])
                for cl in pending:
                    if cl['desc'].strip() == description.strip():
                        LOGGER.debug('Changelist found: {}'.format(cl['change']))
                        change = Changelist(int(cl['change']), self)
                        break
                else:
                    LOGGER.debug('No changelist found, creating one')
                    change = Changelist.create(description, self)
                    change.client = self._client
                    change.save()

        return change

    def add(self, filename, change=None):
        """Adds a new file to a changelist

        :param filename: File path to add
        :type filename: str
        :param change: Changelist to add the file to
        :type change: int
        :returns: :class:`.Revision`
        """
        try:
            if not self.canAdd(filename):
                raise errors.RevisionError('File is not under client path')

            if change is None:
                self.run(['add', filename])
            else:
                self.run(['add', '-c', str(change.change), filename])

            data = self.run(['fstat', filename])[0]
        except errors.CommandError as err:
            LOGGER.debug(err)
            raise errors.RevisionError('File is not under client path')

        rev = Revision(data, self)

        if isinstance(change, Changelist):
            change.append(rev)

        return rev

    def canAdd(self, filename):
        """Determines if a filename can be added to the depot under the current client

        :param filename: File path to add
        :type filename: str
        """
        try:
            result = self.run(['add', '-n', '-t', 'text', filename])[0]
        except errors.CommandError as err:
            LOGGER.debug(err)
            return False

        if result.get('code') not in ('error', 'info'):
            return True

        LOGGER.warn('Unable to add {}: {}'.format(filename, result['data']))

        return False


@six.python_2_unicode_compatible
class PerforceObject(object):
    """Abstract class for dealing with the dictionaries coming back from p4 commands

    This is a simple descriptor for the incoming P4Dict
    """
    def __init__(self, connection=None):
        self._connection = connection or Connection()
        self._p4dict = {}

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u'<{}>'.format(self.__class__.__name__)

    def __repr__(self):
        return self.__unicode__()


class FormObject(PerforceObject):
    """Abstract class for objects with a form api (client, stream, changelist)"""
    READONLY = ()
    COMMAND = ''

    def __init__(self, connection):
        super(FormObject, self).__init__(connection)
        self._dirty = False

    def save(self):
        """Saves the state of the changelist"""
        if not self._dirty:
            return

        fields = []
        formdata = dict(self._p4dict)
        del formdata['code']
        for key, value in six.iteritems(formdata):
            match = re.search('\d$', key)
            if match:
                value = '\t{}'.format(value)
                key = key[:match.start()]

            value = value.replace('\n', '\n\t')
            fields.append('{}:  {}'.format(key, value))
        form = '\n'.join(fields)
        self._connection.run([self.COMMAND, '-i'], stdin=form, marshal_output=False)
        self._dirty = False


class Changelist(PerforceObject):
    """
    A Changelist is a collection of files that will be submitted as a single entry with a description and
    timestamp
    """
    def __init__(self, changelist=None, connection=None):
        connection = connection or Connection()

        super(Changelist, self).__init__(connection=connection)

        self._files = None
        self._dirty = False
        self._reverted = False
        self._change = changelist

        self.query(files=False)

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
        if not isinstance(other, Revision):
            raise TypeError('Value needs to be a Revision instance')

        if self._files is None:
            self.query()

        names = [f.depotFile for f in self._files]

        return other.depotFile in names

    def __getitem__(self, name):
        if self._files is None:
            self.query()

        return self._files[name]

    def __len__(self):
        if self._files is None:
            self.query()

        return len(self._files)

    def __iadd__(self, other):
        if self._files is None:
            self.query()

        if isinstance(other, list):
            currentfiles = self._files[:]
            try:
                files = [str(f) for f in other]
                cmd = ['edit', '-c', str(self.change)]
                self._connection.run(cmd + files)
                self._files += other
                self.save()
            except errors.CommandError:
                self._files = currentfiles
                raise

        return self

    def __eq__(self, other):
        return int(self) == int(other)

    def __format__(self, *args, **kwargs):
        if self._files is None:
            self.query()

        kwargs = {
            'change': self._p4dict['change'],
            'client': str(self._p4dict['client']),
            'user': self._p4dict['user'],
            'status': self._p4dict['status'],
            'description': self._p4dict['description'].replace('\n', '\n\t'),
            'files': '\n'.join(['\t{}'.format(f.depotFile) for f in self._files])
        }

        return FORMAT.format(**kwargs)

    def query(self, files=True):
        """Queries the depot to get the current status of the changelist"""
        if self._change:
            cl = str(self._change)
            self._p4dict = {camel_case(k): v for k, v in six.iteritems(self._connection.run(['change', '-o', cl])[0])}

        if files:
            self._files = []
            if self._p4dict.get('status') == 'pending' or self._change == 0:
                change = self._change or 'default'
                data = self._connection.run(['opened', '-c', str(change)])
                self._files = [Revision(r, self._connection) for r in data]
            else:
                data = self._connection.run(['describe', str(self._change)])[0]
                depotfiles = []
                for k, v in six.iteritems(data):
                    if k.startswith('depotFile'):
                        depotfiles.append(v)
                self._files = self._connection.ls(depotfiles)

    def append(self, rev):
        """Adds a :py:class:Revision to this changelist and adds or checks it out if needed

        :param rev: Revision to add
        :type rev: :class:`.Revision`
        """
        if not isinstance(rev, Revision):
            results = self._connection.ls(rev)
            if not results:
                self._connection.add(rev, self)
                return

            rev = results[0]

        if not rev in self:
            if rev.isMapped:
                rev.edit(self)

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
        if not isinstance(rev, Revision):
            raise TypeError('argument needs to be an instance of Revision')

        if rev not in self:
            raise ValueError('{} not in changelist'.format(rev))

        self._files.remove(rev)
        if not permanent:
            rev.changelist = self._connection.default

    def revert(self, unchanged_only=False):
        """Revert all files in this changelist

        :param unchanged_only: Only revert unchanged files
        :type unchanged_only: bool
        :raises: :class:`.ChangelistError`
        """
        if self._reverted:
            raise errors.ChangelistError('This changelist has been reverted')

        change = self._change
        if self._change == 0:
            change = 'default'

        cmd = ['revert', '-c', str(change)]

        if unchanged_only:
            cmd.append('-a')

        files = [f.depotFile for f in self._files]
        if files:
            cmd += files
            self._connection.run(cmd)

        self._files = []
        self._reverted = True

    def save(self):
        """Saves the state of the changelist"""
        self._connection.run(['change', '-i'], stdin=format(self), marshal_output=False)
        self._dirty = False

    def submit(self):
        """Submits a chagelist to the depot"""
        if self._dirty:
            self.save()

        self._connection.run(['submit', '-c', str(self._change)], marshal_output=False)

    def delete(self):
        """Reverts all files in this changelist then deletes the changelist from perforce"""
        try:
            self.revert()
        except errors.ChangelistError:
            pass

        self._connection.run(['change', '-d', str(self._change)])

    @property
    def change(self):
        return int(self._change)

    @property
    def client(self):
        """Perforce client this changelist is under"""
        return self._p4dict['client']

    @client.setter
    def client(self, client):
        self._p4dict['client'] = client
        self._dirty = True

    @property
    def description(self):
        """Changelist description"""
        return self._p4dict['description'].strip()

    @description.setter
    def description(self, desc):
        self._p4dict['description'] = desc.strip()
        self._dirty = True

    @property
    def status(self):
        return self._p4dict['status']

    @property
    def user(self):
        return self._p4dict['user']

    @property
    def isDirty(self):
        """Does this changelist have unsaved changes"""
        return self._dirty

    @property
    def time(self):
        """Creation time of this changelist"""
        return datetime.datetime.strptime(self._p4dict['date'], DATE_FORMAT)

    @staticmethod
    def create(description='<Created by Python>', connection=None):
        """Creates a new changelist

        :param connection: Connection to use to create the changelist
        :type connection: :class:`.Connection`
        :param description: Description for new changelist
        :type description: str
        :returns: :class:`.Changelist`
        """
        connection = connection or Connection()
        description = description.replace('\n', '\n\t')
        form = NEW_FORMAT.format(client=str(connection.client), description=description)
        result = connection.run(['change', '-i'], stdin=form, marshal_output=False)

        return Changelist(int(result.split()[1]), connection)


class Default(Changelist):
    def __init__(self, connection):
        super(Default, self).__init__(None, connection)

        data = self._connection.run(['opened', '-c', 'default'])

        for f in data:
            if self._files is None:
                self._files = []
            self._files.append(Revision(f, self._connection))

        data = self._connection.run(['change', '-o'])[0]
        self._change = 0
        self._description = data['Description']
        self._client = connection.client
        self._time = None
        self._status = 'new'
        self._user = connection.user

    def save(self):
        """Saves the state of the changelist"""
        files = [f.depotFile for f in self._files]
        cmd = ['reopen', '-c', 'default']
        self._connection.run(cmd + files)
        self._dirty = False


class Revision(PerforceObject):
    """A Revision represents a file on perforce at a given point in it's history"""
    def __init__(self, data, connection=None):
        connection = connection or Connection()

        super(Revision, self).__init__(connection=connection)

        if isinstance(data, six.string_types):
            self._p4dict = {'depotFile': data}
            self.query()
        else:
            self._p4dict = data

        self._head = HeadRevision(self._p4dict)
        self._changelist = None
        self._filename = None

    def __len__(self):
        if 'fileSize' not in self._p4dict:
            self._p4dict = self._connection.run(['fstat', '-m', '1', '-Ol', self.depotFile])[0]

        return int(self._p4dict['fileSize'])

    def __unicode__(self):
        return self.depotFile

    def __repr__(self):
        return '<%s: %s#%s>' % (self.__class__.__name__, self.depotFile, self.revision)

    def __int__(self):
        return self.revision

    def query(self):
        """Runs an fstat for this file and repopulates the data"""

        self._p4dict = self._connection.run(['fstat', '-m', '1', self._p4dict['depotFile']])[0]
        self._head = HeadRevision(self._p4dict)

        self._filename = self.depotFile

    def edit(self, changelist=0):
        """Checks out the file

        :param changelist: Optional changelist to checkout the file into
        :type changelist: :class:`.Changelist`
        """
        command = 'reopen' if self.action in ('add', 'edit') else 'edit'
        if int(changelist):
            self._connection.run([command, '-c', str(changelist.change), self.depotFile])
        else:
            self._connection.run([command, self.depotFile])

        self.query()

    def lock(self, lock=True, changelist=0):
        """Locks or unlocks the file

        :param lock: Lock or unlock the file
        :type lock: bool
        :param changelist: Optional changelist to checkout the file into
        :type changelist: :class:`.Changelist`
        """

        cmd = 'lock' if lock else 'unlock'
        if changelist:
            self._connection.run([cmd, '-c', changelist, self.depotFile])
        else:
            self._connection.run([cmd, self.depotFile])

        self.query()

    def sync(self, force=False, safe=True, revision=0, changelist=0):
        """Syncs the file at the current revision

        :param force: Force the file to sync
        :type force: bool
        :param safe: Don't sync files that were changed outside perforce
        :type safe: bool
        :param revision: Sync to a specific revision
        :type revision: int
        :param changelist: Changelist to sync to
        :type changelist: int
        """
        cmd = ['sync']
        if force:
            cmd.append('-f')

        if safe:
            cmd.append('-s')

        if revision:
            cmd.append('{}#{}'.format(self.depotFile, revision))
        elif changelist:
            cmd.append('{}@{}'.format(self.depotFile, changelist))
        else:
            cmd.append(self.depotFile)

        self._connection.run(cmd)

        self.query()

    def revert(self, unchanged=False):
        """Reverts any file changes

        :param unchanged: Only revert if the file is unchanged
        :type unchanged: bool
        """
        cmd = ['revert']
        if unchanged:
            cmd.append('-a')

        wasadd = self.action == 'add'

        cmd.append(self.depotFile)

        self._connection.run(cmd)

        if 'movedFile' in self._p4dict:
            self._p4dict['depotFile'] = self._p4dict['movedFile']

        if not wasadd:
            self.query()

        if self._changelist:
            self._changelist.remove(self, permanent=True)

    def shelve(self, changelist=None):
        """Shelves the file if it is in a changelist

        :param changelist: Changelist to add the move to
        :type changelist: :class:`.Changelist`
        """
        if changelist is None and self.changelist.description == 'default':
            raise errors.ShelveError('Unabled to shelve files in the default changelist')

        cmd = ['shelve']
        if changelist:
            cmd += ['-c', str(changelist)]

        cmd.append(self.depotFile)

        self._connection.run(cmd)

        self.query()

    def move(self, dest, changelist=0, force=False):
        """Renames/moves the file to dest

        :param dest: Destination to move the file to
        :type dest: str
        :param changelist: Changelist to add the move to
        :type changelist: :class:`.Changelist`
        :param force: Force the move to an existing file
        :type force: bool
        """
        cmd = ['move']
        if force:
            cmd.append('-f')

        if changelist:
            cmd += ['-c', str(changelist)]

        if not self.isEdit:
            self.edit(changelist)

        cmd += [self.depotFile, dest]
        self._connection.run(cmd)
        self._p4dict['depotFile'] = dest

        self.query()

    def delete(self, changelist=0):
        """Marks the file for delete

        :param changelist: Changelist to add the move to
        :type changelist: :class:`.Changelist`
        """
        cmd = ['delete']

        if changelist:
            cmd += ['-c', str(changelist)]

        cmd.append(self.depotFile)
        self._connection.run(cmd)

        self.query()

    @property
    def hash(self):
        """The hash value of the current revision"""
        if 'digest' not in self._p4dict:
            self._p4dict = self._connection.run(['fstat', '-m', '1', '-Ol', self.depotFile])[0]

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
    def isMapped(self):
        """Is the file mapped to the current workspace"""
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
        """Which :class:`.Changelist` is this revision in"""
        if self._changelist:
            return self._changelist

        if self._p4dict['change'] == 'default':
            return Default(connection=self._connection)
        else:
            return Changelist(str(self._p4dict['change']), self._connection)

    @changelist.setter
    def changelist(self, value):
        if not isinstance(value, Changelist):
            raise TypeError('argument needs to be an instance of Changelist')

        if self not in value:
            value.append(self)

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
        """The number, if any, of resolved integration records"""
        return int(self._p4dict.get('resolved', 0))

    @property
    def unresolved(self):
        """The number, if any, of unresolved integration records"""
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
        """The :class:`.HeadRevision` of this file"""
        return self._head

    @property
    def isSynced(self):
        """Is the local file the latest revision"""
        return self.revision == self.head.revision

    @property
    def isEdit(self):
        """Is the file open for edit"""
        return self.action == 'edit'


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
    def time(self):
        return datetime.datetime.fromtimestamp(int(self._p4dict['headTime']))

    @property
    def modifiedTime(self):
        return datetime.datetime.fromtimestamp(int(self._p4dict['headModTime']))


class Client(FormObject):
    """Represents a client(workspace) for a given connection"""
    COMMAND = 'client'

    def __init__(self, client, connection=None):
        super(Client, self).__init__(connection=connection)

        assert client is not None

        results = self._connection.run(['client', '-o', client])[0]
        self._p4dict = {camel_case(k): v for k, v in six.iteritems(results)}

    def __unicode__(self):
        return self.client

    @property
    def root(self):
        """Root path fo the client"""
        return path.Path(self._p4dict['root'])

    @property
    def client(self):
        return self._p4dict['client']

    @property
    def description(self):
        return self._p4dict['description'].strip()

    @description.setter
    def description(self, value):
        self._p4dict['description'] = value.strip()
        self._dirty = True

    @property
    def host(self):
        return self._p4dict['host']

    @host.setter
    def host(self, value):
        self._p4dict['host'] = value
        self._dirty = True

    @property
    def lineEnd(self):
        return self._p4dict['lineEnd']

    @lineEnd.setter
    def lineEnd(self, value):
        self._p4dict['lineEnd'] = value
        self._dirty = True

    @property
    def owner(self):
        return self._p4dict['owner']

    @owner.setter
    def owner(self, value):
        self._p4dict['owner'] = value
        self._dirty = True

    @property
    def submitOptions(self):
        return self._p4dict['submitOptions']

    @submitOptions.setter
    def submitOptions(self, value):
        self._p4dict['submitOptions'] = value
        self._dirty = True

    @property
    def view(self):
        """A list of view specs"""
        spec = []
        for k, v in six.iteritems(self._p4dict):
            if k.startswith('view'):
                match = RE_FILESPEC.search(v)
                if match:
                    spec.append(FileSpec(v[:match.end() - 1], v[match.end():]))

        return spec

    @property
    def access(self):
        """The date and time last accessed"""
        return datetime.datetime.strptime(self._p4dict['access'], DATE_FORMAT)

    @property
    def update(self):
        """The date and time the client was updated"""
        return datetime.datetime.strptime(self._p4dict['update'], DATE_FORMAT)

    @property
    def stream(self):
        """Which stream, if any, the client is under"""
        stream = self._p4dict.get('stream')
        if stream:
            return Stream(stream, self._connection)


class Stream(PerforceObject):
    """An object representing a perforce stream"""
    def __init__(self, stream, connection=None):
        super(Stream, self).__init__(connection=connection)

        assert stream is not None

        results = self._connection.run(['stream', '-o', '-v', stream])[0]
        self._p4dict = {camel_case(k): v for k, v in six.iteritems(results)}

    def __unicode__(self):
        return self._p4dict['stream']

    @property
    def description(self):
        """Stream description tha thas been trimmed"""
        return self._p4dict.get('description', '').strip()

    @property
    def view(self):
        """A list of view specs"""
        spec = []
        for k, v in six.iteritems(self._p4dict):
            if k.startswith('view'):
                match = RE_FILESPEC.search(v)
                if match:
                    spec.append(FileSpec(v[:match.end() - 1], v[match.end():]))

        return spec

    @property
    def access(self):
        """The date and time last accessed"""
        return datetime.datetime.strptime(self._p4dict['access'], DATE_FORMAT)

    @property
    def update(self):
        """The date and time the client was updated"""
        return datetime.datetime.strptime(self._p4dict['update'], DATE_FORMAT)
