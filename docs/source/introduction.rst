Introduction
============

PALM is a library to create clusters of high-performance micro-services with
simple and reusable components. In PALM, all servers are equal, and they have
the same capabilities: inbound and outbound ports, calling conventions, cache, logging, performance
counters... PALM also provides the required infrastructure to configure and
monitor the cluster.

.. only:: html

    .. figure:: _images/cluster.png
        :align: center

.. only:: latex

    .. figure:: _images/cluster.pdf
        :align: center
        :scale: 60

It also adds a connection model for those clusters: a pipeline. A pipeline
is a sequence of servers receiving messages and sending some result to the
following. A Job is a pipeline definition and a set of messages that start
the computation. The item that submits a job is a PALM client. This means
that a pipeline is only part of a job specification, and it is not hardcoded
in the configuration of the cluster. Again, all servers are equal.


.. only:: html

    .. figure:: _images/pipeline.png
        :align: center

.. only:: latex

    .. figure:: _images/pipeline.pdf
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


Authors
-------

PALM is a project developed at `NFQ Solutions <http://nfqsolutions.com>`_.

