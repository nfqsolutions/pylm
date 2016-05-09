The ten thousand feet view
==========================

This has to be updated. A lot.

Introduction and example
------------------------

Assume that your sysadmin has already configured PALM for you, and that you
want to build a cluster with a single RPC server. Let's also assume that you
want to use the Python implementation of PALM, pylm.

PALM servers are are subclasses of other servers that provide a set of
useful methods. A simple RPC server would inherit from ``RegisteredServer``.
Assume that you already have a function called ``very_long_computation`` that
contains your business logic, that you want to expose as a RPC job with the
name ``business_logic``.  Putting it all together in a server it would look
like this.

.. code-block:: python

    from pylm.components import RegisteredServer, run_server

    class SomeServer(RegisteredServer):
        def business_logic(self, message):
            payload = deserialize(message)
            value = very_long_computation(payload)
            return serialize(value)


The functions ``serialize`` and ``deserialize`` just denote that what the
servers get and provide are binary messages.

.. important::

    PALM moves bytes around, not objects. You have to serialize every
    piece of communication between servers. You can use any serialization
    protocol you want, as long as its product is a binary message.

The next step is to tell the system about what you have implemented,
and to run the server. PALM provides a useful function for that.

.. code-block:: python

    # Previous code above

    if __name__ == '__main__':
        run_server(SomeServer, 'my_server', ['business_logic'])

If you put everything in a file called ``server.py``, and you execute the
following command

.. code-block:: bash

    $> python server.py run

the whole system will be aware of this new server, and
it will react accordingly.  You have told the cluster that there
is a new server called ``my_server`` and that a remote job with the name
``business_logic``  is available to any other member of the cluster.


You have just implemented a server. Now you need a client that
communicates with the server. In this case, the role of the client is
to create a bunch of messages, to configure a job, and to submit the
workload to the PALM cluster. It is as simple as follows:

.. code-block:: python

    # Some imports
    client = Client

    def job_generator():
        # This is a generator that produces lots of messages
        # ...
            yield serialize(message)

    client.job(job_generator(), ['my_server.business_logic'])
    client.submit()

And this is it. If you execute the client it will send all the
messages that are created in ``job_generator`` to your
``very_long_computation``. You do not have to configure anything
else. The system will deal with all the tedious work of configuring
the ports, making the connections, adding metadata to the messages...
It does not care where you launch the scripts, either the client or
the server, as long as the node where they run is part of a PALM
cluster.

The cluster is not really useful now, because the results of
``very_long_computation`` are never collected. You will find some complete
examples of clusters that complete a useful workload in the examples section.

What is PALM built upon?
------------------------

PALM is able to do all that magic under the hood because it uses some
cool recent technologies like `etcd <https://github.com/coreos/etcd>`_,
`zeromq <http://zeromq.org/>`_ and
`protobuf <https://developers.google.com/protocol-buffers/?hl=en>`_. You need a
correct installation of all of them to be able to run PALM. There are two
implementations of PALM available, and each implementation supports a
different programming language. At this moment, only Python and Java
are supported.

.. important::

    Supporting a programming language in PALM requires some extra
    work. Python and Java are supported because they are needed by the
    company that funds the development of PALM. If you need any other
    programming language to be supported, please contact the
    developers.

Similar technologies
--------------------

To be updated

The most similar technology to PALM is
`Google's Cloud Dataflow (GCDF) <https://cloud.google.com/dataflow/>`_, although
the goals of PALM are a little more humble.  In GCDF you can connect almost any
service provided by Google, and libraries to connect the stream of data to
external tools are provided. PALM is a series of servers that implement
messaging patterns, that you can use as building blocks to construct a *data
flow*.

PALM is also comparable to `Akka <http://akka.io>`_, since PALM servers can be
considered actors in some way. Akka is also more general; it is a
framework to construct independent actors that can behave anyway you want
them to behave. In short, you could build PALM with Akka, but you could not
build Akka with PALM servers. PALM is opinionated, and the servers support a
more limited amount of actions. One of the selling points of Akka is its
performance. PALM shows similar performance figures, since PALM's message
queue, ZeroMQ, performs decently well under most circumstances. In some
real-world tests, in fact PALM was even faster than Spark, which is based on
Akka.