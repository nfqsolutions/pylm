.. _high-level-api:

High level API
==============

The High level API of pylm exposes a series of servers and clients that you can inherit to
implement different communication and execution models. A simple example of a
standalone server and its communication with the corresponding client can be found in the :ref:`introduction`.

There are three flavors of servers, each one corresponds to a connectivity model.

* :ref:`standalone` connect only to clients

* :ref:`chained` can connect to clients as well as other servers.

* :ref:`pipelined` are part of an infrastructure managed by a registry. The client is able to launch a stream
  of messages and to configure the path along servers that the stream has to follow. They are projected, but they
  have not been implemented yet.

In each of the flavors, a *server* refers to a unique server that connects to a client, while a *parallel server*
refers to the combination of a *master server* and a series of *workers*. A parallel server is able to
distribute the workload among the available workers, in other words, the master does the managing and the
workers do the actual work. You will find a thorough description of each flavor and variant in the following sections.

.. toctree::
    :maxdepth: 2

    standalone
    chained
    pipelined

