Turning a PALM master into a microservice
=========================================

The low level API also includes parts that can be used to turn a master
server into a more classical microserver in the form of an HTTP server. The
goal would be to offer a gateway to a PALM cluster with the HTTP protocol,
meaning that the client can be any HTTP client.

.. only:: html

    .. figure:: _images/parallel_http.png
        :align: center

.. only:: latex

    .. figure:: _images/parallel_http.pdf
        :align: center
        :scale: 60

The components are the :py:class:`pylm.parts.gateways.GatewayRouter`,
:py:class:`pylm.parts.gateways.GatewayDealer` and
:py:class:`pylm.parts.gateways.HttpGateway`. They can be used in the following
fashion to wire a master to listen to an HTTP connection, that is served from
the HttpGateway part.

.. only:: html

    .. figure:: _images/microservice_internals.png
        :align: center

.. only:: latex

    .. figure:: _images/microservice_internals.pdf
        :align: center
        :scale: 60

The whole example can be implemented as follows.

.. literalinclude:: ../../examples/gateway/microservice.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/gateway/worker.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/gateway/client.py
    :language: python
    :linenos: