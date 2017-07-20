.. _examples:

Examples
========

.. _single-server-client:

Simple server and client communication
--------------------------------------

.. only:: html

    .. figure:: _images/single.png
        :align: center

.. only:: latex

    .. figure:: _images/single.pdf
        :align: center
        :scale: 60

.. literalinclude:: ../../examples/single/server.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/single/client.py
    :language: python
    :linenos:

.. _simple-parallel:

Simple parallel server and client communication
-----------------------------------------------

.. only:: html

    .. figure:: _images/parallel.png
        :align: center

.. only:: latex

    .. figure:: _images/parallel.pdf
        :align: center
        :scale: 60

.. literalinclude:: ../../examples/parallel/master.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/parallel/worker.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/parallel/client.py
    :language: python
    :linenos:

Cache operation for the standalone parallel version
---------------------------------------------------

.. literalinclude:: ../../examples/cache/master.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/cache/worker.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/cache/client.py
    :language: python
    :linenos:

Usage of the scatter function
-----------------------------

.. literalinclude:: ../../examples/scatter/master.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/scatter/worker.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/scatter/client.py
    :language: python
    :linenos:

Usage of the gather function
----------------------------

.. literalinclude:: ../../examples/gather/master.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/gather/worker.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/gather/client.py
    :language: python
    :linenos:

.. _pipeline-client:

A pipelined message stream
--------------------------

.. only:: html

    .. figure:: _images/pipeline.png
        :align: center

.. only:: latex

    .. figure:: _images/pipeline.pdf
        :align: center
        :scale: 60

.. literalinclude:: ../../examples/pipeline/server.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/pipeline/pipeline.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/pipeline/client.py
    :language: python
    :linenos:

.. _pipeline-tee:

A pipelined message stream forming a tee
----------------------------------------

.. only:: html

    .. figure:: _images/pipeline-tee.png
        :align: center

.. only:: latex

    .. figure:: _images/pipeline-tee.pdf
        :align: center
        :scale: 60

.. literalinclude:: ../../examples/tee/server.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/tee/pipeline_close.py
    :language: python
    :linenos:

.. important::

    If the method of a pipeline does not return any value, pylm assumes that
    no message has to be delivered

.. literalinclude:: ../../examples/tee/pipeline_echo.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/tee/client.py
    :language: python
    :linenos:


.. _pipeline-stream:

A pipelined message stream forming a tee and controls the stream of messages
----------------------------------------------------------------------------

.. only:: html

    .. figure:: _images/pipeline-stream.png
        :align: center

.. only:: latex

    .. figure:: _images/pipeline-stream.pdf
        :align: center
        :scale: 60

.. literalinclude:: ../../examples/stream/server.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/stream/pipeline_close.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/stream/pipeline_echo.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/stream/client.py
    :language: python
    :linenos:

.. _pipeline-sink:

A pipelined message stream forming a tee and controls the stream of messages with a sink
----------------------------------------------------------------------------------------

.. only:: html

    .. figure:: _images/pipeline-stream-sink.png
        :align: center

.. only:: latex

    .. figure:: _images/pipeline-stream-sink.pdf
        :align: center
        :scale: 60

.. literalinclude:: ../../examples/stream_sink/server.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/stream_sink/pipeline_odd.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/stream_sink/pipeline_even.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/stream_sink/sink.py
    :language: python
    :linenos:
       
.. literalinclude:: ../../examples/stream_sink/client.py
    :language: python
    :linenos:

       
.. _pipeline-master:

Connecting a pipeline to a master
---------------------------------

.. only:: html

    .. figure:: _images/master_pipeline.png
        :align: center

.. only:: latex

    .. figure:: _images/master_pipeline.pdf
        :align: center
        :scale: 60

.. literalinclude:: ../../examples/master_pipeline/master.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/master_pipeline/pipeline.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/master_pipeline/worker.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/master_pipeline/client.py
    :language: python
    :linenos:


.. _server-hub:

Connecting a hub to a server
----------------------------

.. only:: html

    .. figure:: _images/server_hub.png
        :align: center

.. only:: latex

    .. figure:: _images/server_hub.pdf
        :align: center
        :scale: 60

.. literalinclude:: ../../examples/server_hub/server.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/server_hub/hub.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/server_hub/worker.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/server_hub/client.py
    :language: python
    :linenos:

Building a master server from its components
--------------------------------------------

.. only:: html

    .. figure:: _images/master_internals.png
        :align: center

.. only:: latex

    .. figure:: _images/master_internals.pdf
        :align: center
        :scale: 60

.. literalinclude:: ../../examples/template/master.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/template/worker.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/template/client.py
    :language: python
    :linenos:


Turning a master into a web server with the HTTP gateway
--------------------------------------------------------

.. only:: html

    .. figure:: _images/parallel_http.png
        :align: center

.. only:: latex

    .. figure:: _images/parallel_http.pdf
        :align: center
        :scale: 60

.. literalinclude:: ../../examples/gateway/microservice.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/gateway/worker.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/gateway/client.py
    :language: python
    :linenos:


Using server-less infrastructure as workers via the HTTP protocol
-----------------------------------------------------------------

.. only:: html

    .. figure:: _images/http_part.png
        :align: center

.. only:: latex

    .. figure:: _images/http_part.pdf
        :align: center
        :scale: 60

.. literalinclude:: ../../examples/http/master.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/http/web_worker.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/http/client.py
    :language: python
    :linenos:
