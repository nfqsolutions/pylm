Turning a PALM master into a microservice
=========================================

.. only:: html

    .. figure:: _images/parallel_http.png
        :align: center

.. only:: latex

    .. figure:: _images/parallel_http.pdf
        :align: center
        :scale: 60

.. only:: html

    .. figure:: _images/microservice_internals.png
        :align: center

.. only:: latex

    .. figure:: _images/microservice_internals.pdf
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