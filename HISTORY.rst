.. :changelog:

History
-------

0.3.9 (2016-1-29)
--------------------
* Changelist objects are lazy and wil only query files as needed

0.3.7 (2015-1-7)
--------------------
* Fixed bugs regarding spaces in file names or specs
* Fixed bug that may have left too many file handles open
* Added comparison operator to Changelist

0.3.6 (2015-12-3)
--------------------
* Added __iadd_ operator to Changelist
* Added unchanged_only flag to Changelist.revert()
* Added exclude_deleted flag to Connection.ls()
* Fixed a bug on windows that would occur if the command line was too long (>8190)
* Added setter to Connection.client
* Changelist.append will now raise a RevisionError if the file to append is not under the clients root

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
