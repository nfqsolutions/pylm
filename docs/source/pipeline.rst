.. _pipeline:

The Pipeline server
===================

The serial server presented in the previous section is intended to receive
messages from a client. The pipeline server is just like a serial server, but
it is designed to receive a stream of messages from another server, forming a
pipeline. It can then redirect the messages to another server or it can route
the messages back to the client to close the message loop.

The simplest architecture where a Pipeline server is useful is adding an
additional step to a client-server call like the one presented in the
following figure.

.. only:: html

    .. figure:: _images/pipeline.png
        :align: center

.. only:: latex

    .. figure:: _images/pipeline.pdf
        :align: center
        :scale: 60

You can see an example how the Pipeline server to create a pipeline started
by a Server in the examples section (:ref:`pipeline-client`). The big picture
is simple. A Server starts a pipeline, and the pipeline servers are the steps
of it.

One important detail in this first example is that the client gets a sequence
of method calls, the server name and the method of each step, in a list. This
of course means that the first argument of the :func:`pylm.clients.Client.eval`
and :func:`pylm.clients.Client.job` methods in may be either a string or a list
of strings.

Pipeline servers can be attached to Master servers too to attach a
parallel-processing step to a serial-processing step


.. only:: html

    .. figure:: _images/master_pipeline.png
        :align: center

.. only:: latex

    .. figure:: _images/master_pipeline.pdf
        :align: center
        :scale: 60

You can find the full example in :ref:`pipeline-master`

Controlling the messages down the pipeline
------------------------------------------

One important feature of the pipelined message stream is that it can be
controlled and diverted. If one connects multiple pipeline servers to a
single server, the default behavior is to send all messages to all the
connected pipelines.

.. only:: html

    .. figure:: _images/pipeline-tee.png
        :align: center

.. only:: latex

    .. figure:: _images/pipeline-tee.pdf
        :align: center
        :scale: 60

If you take a look at the full example (:ref:`pipeline-tee`), you can see
that the Pipeline needs an extra argument, which is the name of the server or
the pipeline at the previous step. At the same time, one must tell the
servers at its creation that the stream of messages will be sent to a
Pipeline, and not sent back to the client.

If you want a finer-grain control over where each message is sent down the
pipeline you can use the handle_stream method to manage the stream. This can
be used in combination with the ``previous`` option to fully manage the
routing of the messages on each step.

.. only:: html

    .. figure:: _images/pipeline-stream.png
        :align: center

.. only:: latex

    .. figure:: _images/pipeline-stream.pdf
        :align: center
        :scale: 60

You can see the full example here (:ref:`pipeline-stream`).