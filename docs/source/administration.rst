PALM administration guide
=========================

Cluster status information
--------------------------

From now on, we will assume that the pipeliner and the registry units are
running in the same node, and that you have access to a terminal in that
node, that we will job *master*. It is not really necessary that these two
services run in the same node, and the so called *master* node has no
particular feature, but it simplifies some of the explanations in this
chapter.

Now, we will launch a server to see how a running cluster looks like.

.. code-block:: bash

    $> python server.py run

After that, we can see in the registry that PALM has sucessfully configured
the server by checking the logs of the registry and the pipeliner.

.. code-block:: bash
    :emphasize-lines: 7,10

    $> journalctl -n -u registry
    -- Logs begin at Fri 2015-11-06 12:01:43 CET, end at Tue 2016-02-16 11:29:00 CET. --
    Feb 16 11:28:40 nfqbabe registry.py[4559]: INFO:registry:0 servers remaining
    Feb 16 11:28:50 nfqbabe registry.py[4559]: INFO:registry:No servers found
    Feb 16 11:28:50 nfqbabe registry.py[4559]: INFO:registry:0 dead servers
    Feb 16 11:28:50 nfqbabe registry.py[4559]: INFO:registry:0 servers remaining
    Feb 16 11:28:59 nfqbabe registry.py[4559]: INFO:registry:Server e5cd88f7-0f5c-4278-bcc9-fa8caefadbb4 configured
    Feb 16 11:29:00 nfqbabe registry.py[4559]: INFO:registry:Found 1 servers, probing all of them
    Feb 16 11:29:00 nfqbabe registry.py[4559]: INFO:registry:1 servers remaining
    Feb 16 11:29:00 nfqbabe registry.py[4559]: INFO:registry:e5cd88f7-0f5c-4278-bcc9-fa8caefadbb4/printf/registered : b'I,D,I,I,I'
    Feb 16 11:29:00 nfqbabe registry.py[4559]: INFO:registry:0 dead servers
    Feb 16 11:29:00 nfqbabe registry.py[4559]: INFO:registry:1 servers remaining


.. code-block:: bash
    :emphasize-lines: 11

    $> journalctl -n -u pipeliner
    -- Logs begin at Fri 2015-11-06 12:01:43 CET, end at Tue 2016-02-16 11:29:00  CET. --
    Feb 16 11:28:29 nfqbabe pipeliner.py[4560]: INFO:pipeliner:***************************
    Feb 16 11:28:39 nfqbabe pipeliner.py[4560]: CRITICAL:pipeliner:You have no server running
    Feb 16 11:28:39 nfqbabe pipeliner.py[4560]: INFO:pipeliner:***** List of servers *****
    Feb 16 11:28:39 nfqbabe pipeliner.py[4560]: INFO:pipeliner:***************************
    Feb 16 11:28:49 nfqbabe pipeliner.py[4560]: CRITICAL:pipeliner:You have no server running
    Feb 16 11:28:49 nfqbabe pipeliner.py[4560]: INFO:pipeliner:***** List of servers *****
    Feb 16 11:28:49 nfqbabe pipeliner.py[4560]: INFO:pipeliner:***************************
    Feb 16 11:28:59 nfqbabe pipeliner.py[4560]: INFO:pipeliner:***** List of servers *****
    Feb 16 11:28:59 nfqbabe pipeliner.py[4560]: INFO:pipeliner:e5cd88f7-0f5c-4278-bcc9-fa8caefadbb4: Server printf of type registered, implements ['prin
    Feb 16 11:28:59 nfqbabe pipeliner.py[4560]: INFO:pipeliner:***************************


If the server is listed in the registry, then it means that it is alive and
it is listening to messages. If the server is listed in the pipeline it is
accessible to the clients.

PALM has assigned that server the UUID ``e5cd88f7-0f5c-4278-bcc9-fa8caefadbb4``,
that will be from now on the way to identify the server within the cluster.
We can look into the guts of PALM by looking what it is actually stored in
the etcd database. The command for that is ``etcdctl``, and the directory
where the server information is stored is ``/servers``.

.. code-block:: bash

    $> etcdctl ls /servers
    /servers/e5cd88f7-0f5c-4278-bcc9-fa8caefadbb4

    $> etcdctl get /servers/e5cd88f7-0f5c-4278-bcc9-fa8caefadbb4
    {"host": "127.0.0.1", "pid": 4749, "when": "2016-02-16T11:28:59.088608",
    "leader": "e5cd88f7-0f5c-4278-bcc9-fa8caefadbb4", "server": "printf",
    "ports": [5555], "kind": "registered", "functions": ["printf", "_ping",
    "_log_query", "get", "set", "append", "delete"],
    "uuid": "e5cd88f7-0f5c-4278-bcc9-fa8caefadbb4", "configured": true}

This is all the information the system has, and needs, about the server.

Logging
-------

In the previous section you have seen how logging is managed in PALM. Since
the registry and the pipeliner are systemd units, the logs are read with the
``journalctl`` tool. Use the ``-u`` argument to select the unit.

Clear data
----------

The registry should clean up from the system all the servers that are
malfunctioning or dead. After killing one of the servers, the registry should
know.

.. code-block:: bash
    :emphasize-lines: 9

    $> journalctl -n -u registry
    -- Logs begin at Fri 2015-11-06 12:01:43 CET, end at Tue 2016-02-16 15:59:06  CET. --
    Feb 16 15:58:43 nfqbabe registry.py[4559]: INFO:registry:1 servers remaining
    Feb 16 15:58:53 nfqbabe registry.py[4559]: INFO:registry:Found 1 servers, probing all of them
    Feb 16 15:58:53 nfqbabe registry.py[4559]: INFO:registry:1 servers remaining
    Feb 16 15:58:53 nfqbabe registry.py[4559]: INFO:registry:e5cd88f7-0f5c-4278-bcc9-fa8caefadbb4/printf/registered : b'I,I,I'
    Feb 16 15:58:53 nfqbabe registry.py[4559]: INFO:registry:0 dead servers
    Feb 16 15:58:53 nfqbabe registry.py[4559]: INFO:registry:1 servers remaining
    Feb 16 15:59:01 nfqbabe registry.py[4559]: INFO:registry:Deleted server e5cd88f7-0f5c-4278-bcc9-fa8caefadbb4 because it killed itself
    Feb 16 15:59:03 nfqbabe registry.py[4559]: INFO:registry:No servers found
    Feb 16 15:59:03 nfqbabe registry.py[4559]: INFO:registry:0 dead servers
    Feb 16 15:59:03 nfqbabe registry.py[4559]: INFO:registry:0 servers remaining


In some extreme cases, some servers may be still running, but they may be non
responsive to the registry. You can clear them manually from the system by
deleting the entry in the etcd database

.. code-block:: bash

    $> etcdctl rm /servers/e5cd88f7-0f5c-4278-bcc9-fa8caefadbb4

In the case of complete misconfiguration, which is very improbable, you can
reset the cluster by deleting all the information about the servers

.. code-block:: bash

    $> etcdctl rm /servers --recursive

and restarting the PALM services that monitor and configure the servers and the
pipelines.

.. code-block:: bash

    $> systemctl restart registry
    $> systemctl restart pipeliner