Introduction
============

But let's start with something basic, a server and a client able to call one of the server's methods. Much in the
fashion of a RPC server.

.. only:: html

    .. figure:: _images/standalone_single.png
        :align: center

.. only:: latex

    .. figure:: _images/standalone_single.pdf
        :align: center
        :scale: 60

With pylm, the first step is to create the server by subclassing one of the available templates in the high-level API:

.. literalinclude:: ./examples/standalone_single/server.py
    :language: python
    :linenos:

Secondly, we create the client that connects to the server and calls the ``foo`` function from the server.

.. literalinclude:: ./examples/standalone_single/client.py
    :language: python
    :linenos:

It does not care in which order you start the client and the server, pylm
uses ZeroMQ sockets for all the connections, that deal with all the details.
Pylm uses ZeroMQ extensively, and somehow, it also follows its philosophy.

This is what we get when we start the server::

    $> python server.py
    2016-08-09 07:34:53,205 - my_server - WARNING - Got a message

And the client::

    $> python client.py
    Client got: b'you sent me a message'

Which is what we expected. The function ``foo`` only picks what is sent from the client,
and adds it to ``you sent me``. As simple as it seems. However, this basic example
allows us to discover some important aspects of pylm.

* All messages are binary, represented as a sequence of bytes. This means that
  you decide how to serialize and deserialize the data you send to the server.
  If I decided to send a number instead of a sequence of bytes
  (replacing line 6 for ``result = client.job('foo', 1)``), the client would
  crash with a *TypeError*.

* The server inherits from :py:class:`pylm.standalone.servers.Server`. This parent
  class includes some interesting capabilities so you don't have to deal with
  health monitoring, logging, performance analysis and so on. Maybe you don't need
  all these things with a single server, but they become really handy when you
  have to monitor hundreds of microservers.

* The philisopy of pylm has two main principles:

  #. Simple things must be simple. If you don't need something, you just ignore it
     and the whole system will react accordingly.

  #. Pylm is a framework, and does not come with any imposition that is not strictly
     necessary. Use the deployment system of your choice, the infrastructure you
     want... Pylm gives you the pieces to create the cluster, and you are in charge
     of the rest.

But this framework is not designed to create a single server, but hundreds of
them in a complex configuration. An extension of the previous example is to
build a pipeline of servers, each one connected to the previous one.

.. only:: html

    .. figure:: _images/pipeline_single.png
        :align: center

.. only:: latex

    .. figure:: _images/pipeline_single.pdf
        :align: center
        :scale: 60




The magic of PALM is half hidden within the servers. There are five kind of
server templates, that you must subclass to implement your business logic.
Some of them are designed to be a step in the pipeline, while others are
able to perform a parallel multiple-step reduction based on the data of the
message stream, or a self-balancing ventilator-sink parallel computation. In
consequence, PALM can be used to build custom applications with dynamic
parallelism, with some of the nice features expected in high performance
applications: efficient messaging, memory efficiency, load balancing and so on.

The pipeline is a powerful concept, but it takes some effort to configure. For
this reason PALM provides a stripped-down version of the servers that can be
configured manually to work completely standalone. This variant is particularly
convenient when testing. If the computation pipeline works in the standalone case,
it will also work as a step of a pipeline.

Data-parallel and task-parallel
-------------------------------

Distributed architectures are often classified as data-parallel, where the data
domain is partitioned and each chunk is crunched by a separated node; and task-parallel,
where a group of tasks transforms a stream of messages. The first set includes
many map-reduce libraries like Hadoop and Spark, while the second one includes
streaming libraries like Storm and Flink. This separation is more often philosophical
than technical, and PALM does not follow it in any way. Data-parallel tend to use
domain decomposition, but PALM uses messages. Task-parallel is usually implemented
as a graph of stateless servers, but PALM servers are stateful.

The ambitious goal here is to fetch the best of each side of the big-data ecosystem
to provide powerful patterns to design and to implement distributed applications.

Pylm
----

Pylm is the python implementation of the PALM servers, and provides the
fundamental infrastructure to run a PALM cluster. Pylm is also the reference
implementation of all the components. A second complete implementation of the
PALM servers is also being implemented in Java, and it is called
`palm-java <https://bitbucket.org/ekergy/palm-java>`_ (Redirects to private
Bitbucket repository).

