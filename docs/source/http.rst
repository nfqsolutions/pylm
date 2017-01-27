Using HTTP
==========

The default transport to connect the different parts of PALM is ZeroMQ over tcp. Some organizations may not find
that suitable for all cases. For instance, it may be necessary to secure servers with encrypted connections,
or some servers may have to run behind traffic-sniffing firewalls. You name it.

For this reason, pylm includes two parts

.. literalinclude:: ../../examples/http/master.py
    :language: python
    :linenos:


The

.. literalinclude:: ../../examples/http/web_worker.py
    :language: python
    :linenos:


.. literalinclude:: ../../examples/http/client.py
    :language: python
    :linenos:

.. code::

    $> gunicorn -w 4 -b 127.0.0.1:8888 web_worker:app
