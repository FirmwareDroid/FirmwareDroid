Database Overview
=================

The folder ``/FirmwareDroid/models`` contains all the Document-Object Mapper classes for mongoengine. These models are
used for retrieving and storing data from and to the MongoDB database. Similar to an ORM all the model classes are
mapped directly to the database. For more information about Mongoengine see the official documentation:
http://docs.mongoengine.org/

Naming conventions
------------------

 * Foreign keys to other database models are always named with ``_reference`` at the end of the variable. Foreign keys are always use referenced by using mongoengines ``LazyReferenceField`` field to improve performance.
 * List and dict variables always end with ``_list`` or ``_dict``.
    * Variable names never use the plural form to avoid variable confusion. For example, ``names -> name_list``
 * Boolean variables always start with ``is_`` or ``has_``. For example, ``is_external``.

Database Models
-----------------
.. autosummary::
    :toctree: _autosummary
    :recursive:

    model