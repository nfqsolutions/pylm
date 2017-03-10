Using HTTP
==========

The default transport to connect the different parts of PALM is ZeroMQ over
tcp. Some organizations may not find that suitable for all cases. For
instance, it may be necessary to secure servers with encrypted connections,
or some servers may have to run behind traffic-sniffing firewalls, or you
want to exploit a server-less architecture for the workers... You name it.

For this reason, pylm includes two parts to communicate with workers with the
HTTP protocol to create a pipeline with that combines ZMQ sockets over TCP
and HTTP.

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


Pylm provides a way to implement a worker in a very similar fashion to the
previous workers that were shown, and to obtain a WSGI application from it.
If you are not familiar with WSGI, it is a standarised way in which Python
applications are able to talk with web servers.

.. literalinclude:: ../../examples/http/web_worker.py
    :language: python
    :linenos:


.. literalinclude:: ../../examples/http/client.py
    :language: python
    :linenos:

Since the worker is now a WSGI application, you can run it with the web
server of your choice.

.. code::

    $> gunicorn -w 4 -b 127.0.0.1:8888 web_worker:app
