"""Connection object.  This can be specified and cached or can be created"""


import os
import marshal
import subprocess

from perforce import errors
from perforce import revision
from perforce import changelist


__CONNECTION = None


class Connection(object):
    def __init__(self, executable='p4', port=None, client=None, level=1):
        self._executable = executable
        self._port = port or os.getenv('P4PORT', 'localhost:1666')
        self._client = client or os.getenv('P4CLIENT', '')
        self._user = 'bdixon'
        self._level = level

    @property
    def client(self):
        return self._client

    @property
    def user(self):
        return self._user

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = value

    def run(self, cmd, stdin=None, marshal_output=True):
        """Runs a p4 command and returns a list of dictionary objects"""
        records = []
        command = [self._executable, "-p", self._port, "-c", self._client]
        if marshal_output:
            command.append('-G')
        command += cmd.split()

        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=4096)

        if stdin:
            proc.stdin.write(stdin)
        proc.stdin.close()

        if marshal_output:
            try:
                while True:
                    record = marshal.load(proc.stdout)
                    if record.get('code', '') == 'error' and record['severity'] <= self._level:
                        raise errors.CommandError(record['data'])
                    records.append(record)
            except EOFError:
                pass

            stdout, stderr = proc.communicate()
        else:
            records, stderr = proc.communicate()

        if stderr:
            raise errors.CommandError(stderr, command)

        return records

    def ls(self, files):
        if not isinstance(files, (tuple, list)):
            files = [files]

        results = self.run('fstat {0}'.format(' '.join(files)))

        return [revision.Revision(r, self) for r in results]

    def findChangelist(self, description=None):
        if description is None:
            change = changelist.Default(self)
        else:
            if isinstance(description, (int)):
                change = changelist.Changelist(self, description)
            else:
                pending = self.run('changes -s pending')
                for cl in pending:
                    if cl['desc'].strip() == description.strip():
                        change = changelist.Changelist(self, int(cl['change']))
                        break
                else:
                    change = changelist.create(self)
                    change.description = description
                    change.client = self._client
                    change.save()

        return change

    def add(self, filename, change=None):
        try:
            if change is not None:
                self.run('add -c %i %s' % (int(change), filename))
            else:
                self.run('add %s' % filename)

            data = self.run('fstat {}'.format(filename))[0]
        except errors.CommandError:
            raise errors.RevisionError('File is not under client path')
        
        rev = revision.Revision(data, self)

        if isinstance(change, changelist.Changelist):
            change.append(rev)

        return rev


def connect():
    global __CONNECTION
    if __CONNECTION is None:
        __CONNECTION = Connection()

    return __CONNECTION
