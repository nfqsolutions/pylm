Introduction
============

Simple client-server communication
----------------------------------

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

Composition with a pipeline
---------------------------

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

This is one of the ways in which a distributed system can use function composition. The
client calls the function ``foo`` in the first server ``step1``, that then passes the result
as an argument to the function ``bar`` of the second server ``step2``. Finally, the stream
of messages calls the final server called ``last``, that sends the result back to the client.

The standalone server of the previous example is designed to interact solely with a client,
this is the reason why a different set of servers are available in pylm, the chained servers
(:py:class:`pylm.chained.servers.Server`).

.. literalinclude:: ./examples/chained_single/step1.py
    :language: python
    :linenos:

.. literalinclude:: ./examples/chained_single/step2.py
    :language: python
    :linenos:

The last server of the pipeline is slightly different, since it does not chain with another
server, but with the client. It has to inherit from :py:class:`pylm.chained.servers.LastServer`

.. literalinclude:: ./examples/chained_single/last.py
    :language: python
    :linenos:

Finally, the client is slightly different too, and inherits from :py:class:`pylm.chained.client.LoopClient`.
The chained servers do not follow a request reply
pattern, that is valid only between two peers. The client sends the job asynchronously
and waits for the result, without the need to wait for the whole pipeline to finish. This means
that, if the pipeline is complex enough, the results may arrive in a different order than the
jobs they were sent from.

.. literalinclude:: ./examples/chained_single/client.py
    :language: python
    :linenos:

Here is the successive output of the servers and the client:

Step1::

    $> python step1.py
    2016-08-09 12:34:14,944 - step1 - DEBUG - step1 Waiting for a message
    2016-08-09 12:34:22,151 - step1 - DEBUG - step1 Got a message
    2016-08-09 12:34:22,151 - step1 - DEBUG - Looking for foo
    2016-08-09 12:34:22,151 - step1 - WARNING - Got a message
    2016-08-09 12:34:22,151 - step1 - DEBUG - step1 Waiting for a message

Step2::

    $> python step2.py
    2016-08-09 12:34:16,446 - step2 - DEBUG - step2 Waiting for a message
    2016-08-09 12:34:22,151 - step2 - DEBUG - step2 Got a message
    2016-08-09 12:34:22,152 - step2 - DEBUG - Looking for bar
    2016-08-09 12:34:22,152 - step2 - WARNING - Got a message
    2016-08-09 12:34:22,152 - step2 - DEBUG - step2 Waiting for a message

Last::

    $> python last.py
    2016-08-09 12:34:18,416 - last - DEBUG - last Waiting for a message
    2016-08-09 12:34:22,152 - last - DEBUG - last Got a message
    2016-08-09 12:34:22,152 - last - DEBUG - Looking for baz
    2016-08-09 12:34:22,152 - last - WARNING - Got a message
    2016-08-09 12:34:22,153 - last - DEBUG - last Waiting for a message

Client::

    $> python client.py
    Client with the following connections:
     *Listening to input from tcp://127.0.0.1:5561
     *Sending jobs to tcp://127.0.0.1:5555
    Client got:  b'ACK: got it too, after you sent me a message'

The chained servers have to be configured manually, which can be tedious somehow.
This pipeline is technically a streaming service, but without some of the features
of popular libraries for stream computing like Storm or Flink. Pylm is based
on small components that can be combined to create complex servers, and features
like fault-tolerance, logging, configuration (so you don't have to connect the ports yourself)
or deployment are just components that can be used orignored.

These examples are a very small set of the capabilities of pylm. We have not covered the
patterns that support parallel execution of jobs yet. To learn what are the functionalities
of the different servers that are already implemented in pylm, visit the section about
the :ref:`high-level-api`.

If you want to understand the underlying principles and algorithms of the small components
that are used to implement a palm microservice, visit the section about the low-level API.

