Server features
===============

All servers have built-in features that are useful to build a manageable cluster. This section explains how to
use and to configure them. It builds upon the examples of :ref:`standalone`.

Errors
------

You are probably wondering what happens if there is a bug in any of your functions and you

Logging
-------

Each server, independently on its variant, has a built-in logger with the usual Python's logging levels. You can
find them in the :py:mod:`logging` module of the standard library. The following example, that builds upon the
previous one illustrates how to use the logging capabilities.

.. literalinclude:: ./examples/logging/master.py
    :language: python
    :linenos:
    :emphasize-lines: 18, 19, 31

The server sets the ``WARNING`` logging level, and then logs as critical when it changes the payload of the last
message.

.. literalinclude:: ./examples/logging/worker.py
    :language: python
    :linenos:
    :emphasize-lines: 15

The worker server implementation just adds a counter, and each time it processes ten messages, it logs as *info*
the number of messages processed. The output of the master is then::

    $> python master.py
    2016-08-26 08:08:38,679 - server - CRITICAL - Changing the payload of the message

And the output of any of the workers (the two workers are probably doing exactly the same amount of work) is::

    $> python worker.py worker1
    2016-08-26 08:08:38,672 - worker1 - INFO - Processed 10 messages


Endpoints
---------

The size of your cluster may easily grow to tens or hundreds of servers, all of them logging important information
to each one's stdout. This is not a big deal if you already have a good distributed log collector in your
infrastructure, but this may not be the case. The logging infrastructure may be some of the last things you add to
your cluster.