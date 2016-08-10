.. _chained:

Chained servers
===============

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
(:py:class:`pylm.chained.servers.Server`). The first server is analogous to the one in the
previous example, it prepends the string *you sent me* to the original message.

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

Note that, while pylm is in beta stage, the default is to output lots and lots
of debug information.

The chained servers have to be configured manually, which can be tedious sometimes.
This pipeline is technically a streaming service, but without some of the features
of popular libraries for stream computing like Storm or Flink. Pylm is based
on small components that can be combined to create complex servers, and features
like fault-tolerance, logging, configuration (so you don't have to connect the ports yourself)
or deployment are just components that can be used or ignored.

