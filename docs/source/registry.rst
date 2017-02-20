Adapting your components to the pylm registry
=============================================

If you plan to run moderately complex clusters of PALM components, you have
to take a look at `the pylm registry <https://github
.com/nfqsolutions/pylm-registry>`_. The registry is a centralized service
that manages the configuration, the execution and the monitoring of
components.

The central registry is a web service that stores the following things:

* The configuration file of the cluster

* The status of the configuration of the cluster, useful to check if enough
  servers have been added to it.

* The output of all the components that were launched with the runner, a
  script provided by the registry.

To use the capabilities of the registry you have to turn your components in
executable scripts in a particular way. Despite you can force the runner to
run almost anything, we recommend you to follow these simple guidelines.

* Turn each component into an executable script. It may be the usual python
  script starting with the shebang or an entry point in your ``setup.py``.

* Use :py:class:`argparse.ArgumentParser` to let the script get the
  runtime arguments

* To allow testing your script, it is a good practice to define a main
  function that then is called with the usual ``if __name__...``.

What follows is a simple example that adapts the components of a simple
parallel server that can be found here (:ref:`simple-parallel`).

.. literalinclude:: ../../examples/applications/master.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/applications/worker.py
    :language: python
    :linenos:

.. literalinclude:: ../../examples/applications/launcher.py
    :language: python
    :linenos:

From the testing point of view, there is little difference on how to run the
master::

    $> python master.py --name foo
    2017-02-01 10:11:41,485 - root - INFO - Starting the router
    2017-02-01 10:11:41,485 - root - INFO - Starting inbound part Pull
    2017-02-01 10:11:41,485 - root - INFO - Starting inbound part WorkerPull
    2017-02-01 10:11:41,485 - root - INFO - Starting outbound part WorkerPush
    2017-02-01 10:11:41,485 - root - INFO - Starting outbound part Pub
    2017-02-01 10:11:41,485 - root - INFO - Starting bypass part Cache
    2017-02-01 10:11:41,485 - root - INFO - Launch router
    2017-02-01 10:11:41,485 - root - INFO - Inbound Pull connects to WorkerPush
    2017-02-01 10:11:41,486 - root - INFO - b'Pull' successfully started
    2017-02-01 10:11:41,486 - root - INFO - Inbound WorkerPull connects to Pub
    2017-02-01 10:11:41,486 - root - INFO - b'WorkerPull' successfully started
    2017-02-01 10:11:41,486 - root - INFO - b'WorkerPush' successfully started
    2017-02-01 10:11:41,487 - root - INFO - Outbound WorkerPush connects to exterior
    2017-02-01 10:11:41,487 - root - INFO - b'Pub' successfully started
    2017-02-01 10:11:41,488 - root - INFO - Outbound Pub connects to exterior

The worker::

    $> python worker.py
    2017-02-01 10:12:16,674 - e29029... - INFO - Got worker push address: ...
    2017-02-01 10:12:16,674 - e29029... - INFO - Got worker pull address: ...

And the client in the form of a launcher::

    $> python launcher.py --server test --function foo
    2017-02-01 10:12:18,394 - INFO - Fetching configuration from the server
    2017-02-01 10:12:18,394 - INFO - CLIENT 29796938-e3d7-4f9a-b69b...
    2017-02-01 10:12:18,395 - INFO - CLIENT 29796938-e3d7-4f9a-b69b...
    b'e29029a3-6943-4797-a8c2-6005134d8228 processed a message'
    b'e29029a3-6943-4797-a8c2-6005134d8228 processed a message'
    b'e29029a3-6943-4797-a8c2-6005134d8228 processed a message'
    b'e29029a3-6943-4797-a8c2-6005134d8228 processed a message'
    b'e29029a3-6943-4797-a8c2-6005134d8228 processed a message'
    b'e29029a3-6943-4797-a8c2-6005134d8228 processed a message'
    b'e29029a3-6943-4797-a8c2-6005134d8228 processed a message'
    b'e29029a3-6943-4797-a8c2-6005134d8228 processed a message'
    b'e29029a3-6943-4797-a8c2-6005134d8228 processed a message'
    b'e29029a3-6943-4797-a8c2-6005134d8228 processed a message'

With the addition that now the components are ready to be run with the registry.