===============================
Python Perforce
===============================

Pure python perforce API

* Free software: MIT license
* Documentation: https://python-perforce.readthedocs.org.

Features
--------

* Pythonic api to Perforce
* Pure python, no compiled extension

Usage
-----

    >>> from perforce import connect
    >>> p4 = connect()
    >>> revisions = p4.ls('//depot/path/to/file.txt')
    >>> print(revisions)
    [<Revision 1: file.txt>]
    >>> p4.ls('//depot/path/....txt')
    [<Revision 1: file.txt>, <Revision 2: foo.txt>]
    >>> cl = p4.findChangelist('my description')
    >>> with cl:
    ...     cl.append(revisions[0])
    ...     p4.add('path/to/add.txt', cl)
    >>> cl.description
    'my description'
    >>> cl.description = 'something else'
    >>> cl.submit()
