.. _examples:

Examples
========

.. _single-server-client:

Simple server and client communication
--------------------------------------

.. literalinclude:: ../../examples/single/server.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/single/client.py
    :language: python
    :linenos:

.. _simple-parallel:

Simple parallel server and client communication
-----------------------------------------------

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

.. _pipeline-master:

Connecting a pipeline to a master
---------------------------------

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

.. literalinclude:: ../../examples/http/master.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/http/web_worker.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/http/client.py
    :language: python
    :linenos:
