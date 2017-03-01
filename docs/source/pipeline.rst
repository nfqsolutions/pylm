.. _pipeline:

The Pipeline server
===================

.. only:: html

    .. figure:: _images/pipeline.png
        :align: center

.. only:: latex

    .. figure:: _images/pipeline.pdf
        :align: center
        :scale: 60

You can see an example how the Pipeline server to create a pipeline started
by a Server in the examples section (:ref:`pipeline-client`).

.. only:: html

    .. figure:: _images/master_pipeline.png
        :align: center

.. only:: latex

    .. figure:: _images/master_pipeline.pdf
        :align: center
        :scale: 60

A pipeline server can be connected to a master too (:ref:`pipeline-master`)

Tee
---

One important feature of the pipelined message stream is that it can be
controlled and diverted.

.. only:: html

    .. figure:: _images/pipeline-tee.png
        :align: center

.. only:: latex

    .. figure:: _images/pipeline-tee.pdf
        :align: center
        :scale: 60

(:ref:`pipeline-tee`)

Controlling the stream of messages
----------------------------------

You can use the handle_stream method to manage the stream.

.. only:: html

    .. figure:: _images/pipeline-stream.png
        :align: center

.. only:: latex

    .. figure:: _images/pipeline-stream.pdf
        :align: center
        :scale: 60

(:ref:`pipeline-stream`)