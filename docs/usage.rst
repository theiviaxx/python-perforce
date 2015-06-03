========
Usage
========

To use Python Perforce in a project::

    >>> from perforce import connection
    >>> p4 = connection.Connection()
    >>> revisions = p4.files('//depot/path/to/file.txt')
    >>> print(revisions)
    [<Revision 1: file.txt>]
    >>> p4.files('//depot/path/....txt')
    [<Revision 1: file.txt>, <Revision 2: foo.txt>]
    >>> cl = p4.findChangelist('my description')
    >>> with cl:
    ...     cl.append(revisions[0])
    ...     p4.add('path/to/add.txt', cl)
    >>> cl.description
    'my description'
    >>> cl.description = 'something else'
    >>> cl.submit()