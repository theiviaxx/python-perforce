.. :changelog:

History
-------

0.3.5 (2015-11-18)
--------------------

* Changed the argument order for Revisions to be consistent with everything else.  Supports backwards compatible argument orders
* Fixed bug that would attempt to checkout files when querying a changelist

0.3.4 (2015-11-17)
--------------------

* Changed enums to be namedtuples
* Fixed bug when detecting login state

0.3.3 (2015-11-16)
---------------------

* Corrected the way the error levels were being handled
* Added more documentation
* Connection will no longer fail if any of the paramter were incorrect, use Connection.status() to check the status of the connection

0.1.0 (2014-10-16)
---------------------

* First release on PyPI.
