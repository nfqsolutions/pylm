.. _high-level-api:

High level API
==============

The High level API of pylm exposes a series of servers and clients that you can inherit to
implement different communication and execution models. A simple example of a
standalone server and its communication with the corresponding client can be found in the :ref:`introduction`.

In each of the flavors, a *single server* refers to a unique server that connects to a client, while a *parallel server*
refers to the combination of a *master server* and a series of *workers*. A parallel server is able to
distribute the workload among the available workers, in other words, the master is in charge of the management and the
workers do the actual work. You will find a thorough description of each flavor and variant in the following sections.

All servers, regardless of their flavor, have a set of useful tools, documented in :ref:`features`. You can also visit
the section devoted to :ref:`workers` if yow want to know the details of those simpler pieces that do the actual work.

.. toctree::
    :maxdepth: 2

    servers
    message
    features
    clients
    workers
    pipeline
    hub
