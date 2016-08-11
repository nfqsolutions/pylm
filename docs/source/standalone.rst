.. _standalone:

Standalone servers
==================

An example of the simplest standalone server was presented in the :ref:`introduction`. A single server running
in a single process may be useful, but there are a million alternatives to pylm for that. The real usefulness
of pylm arrives when the workload is so large that a single server is not capable of handling it. Here we introduce
parallelism for the first time with the parallel standalone server.



.. only:: html

    .. figure:: _images/standalone_parallel.png
        :align: center

.. only:: latex

    .. figure:: _images/standalone_parallel.pdf
        :align: center
        :scale: 60


.. literalinclude:: ./examples/standalone_parallel/master.py
    :language: python
    :linenos:

.. literalinclude:: ./examples/standalone_parallel/worker.py
    :language: python
    :linenos:

.. literalinclude:: ./examples/standalone_parallel/client.py
    :language: python
    :linenos:


client::

    $> python client.py
    Client with the following connections:
     *Listening to input from tcp://127.0.0.1:5556
     *Sending jobs to tcp://127.0.0.1:5555
    b'worker2 processed a message'
    b'worker1 processed a message'
    b'worker2 processed a message'
    b'worker1 processed a message'
    b'worker2 processed a message'
    b'worker1 processed a message'
    b'worker2 processed a message'
    b'worker1 processed a message'
    b'worker2 processed a message'
    b'worker1 processed a message'

go on 0000000000600922