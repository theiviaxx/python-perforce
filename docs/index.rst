.. python-perforce documentation master file, created by
   sphinx-quickstart on Tue Jul  9 22:26:36 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Python Perforce's documentation!
===========================================

::

    >>> from perforce import connection
    >>> p4 = connection.Connection()
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

API Documentation:

.. toctree::
   :maxdepth: 1

   api
   models
   errors

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
