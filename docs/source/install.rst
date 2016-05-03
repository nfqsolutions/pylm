How to install and to run PALM
==============================

Dependencies
------------

Python
......

You need Python to run PALM, even if you implement your servers in
Java or any other language that is supported in the future. The reason
is that, for PALM to provide all its magic, some services that are
implemented in Python must be running all the time. Python 2.7 and 3.2
(or newer) are supported. Pypy should work as well, but it has not
been tested.

The installation script should be able to deal with the required Python
modules.

etcd
....

Etcd is used to store the global information about the cluster. It is
one of the key components, and PALM will refuse to run at all without
etcd installed and running in your cluster. PALM has been tested with
etcd 2.1 and 2.2.

ZeroMQ
......

The components of PALM communicate each other via messages. Those
messages are delivered via ZeroMQ sockets. This means that PALM
inherits the limitations of ZeroMQ for moving messages
around. Remember, ZeroMQ is a library, and it does not require to
start any daemon, broker or whatsoever.

PALM requires the development libraries of ZeroMQ.

Protocol Buffers
................

As we just said, there will be lots of messages. All of them will be
encoded with Protocol Buffers (PB). This is an opinionated
choice. PALM may connect static and dynamic languages, and we think
that PB provides the best type safety when dealing with message
serialization.

.. important::

    Protocol Buffers is how PALM serializes the messages internally. That
    does not mean that you have to use the same serialization for your
    applications. You can use anything, like messagepack or json.

Leveldb
.......

Every PALM server has a persistency mechanism in the form of an embedded
leveldb key-value store. The installation process compiles the Python
bindings of leveldb (``plyvel``), therefore, PALM requires the development
libraries of leveldb.

Installing PALM
---------------

The easy way
............

Download the `tar.gz` file with the version of choice from the
Bitbucket's downloads section. Then, install the packages (as
superuser) with

.. code-block:: bash

  $> pip install PALM-v.v.v.tar.gz

The hard way
............

You can install and test the development version cloning the
mercurial repository and installing it as superuser.

.. code-block:: bash

  $> hg clone https://guillemborrell@bitbucket.org/ekergy/palm-python
  $> cd palm-python
  $> sudo pip install .

At this point, only Linux is supported.

Running PALM services
---------------------

Before you try to run anything related with PALM, you must have etcd
running. If you are setting up a complete cluster, remember that
running a full etcd installation requires to read
`some extra documentation <https://coreos.com/etcd/docs/latest/>`_.
If you only want to set up a development environment, running a
standalone instance of etcd is just fine.

Once you have a running installation of etcd on each node of your
cluster, and Python, ZeroMQ and PB installed, you are good to go.

The first step is to run the registry daemon. The registry takes care
of the health of the cluster. If a server pops out in the system, the
registry configures it. If another server dies for whatever reason,
the registry cleans the global cluster state. If you have installed
PALM properly, it should be in your ``$PATH``. Running the registry is
as easy as

.. code-block:: bash
		
  $> registry.py run

Finally, you have to run the pipeliner daemon too. The pipeliner
listens to the PALM clients, and tells the cluster that a job has been
submitted.

.. code-block:: bash

  $> pipeliner.py run

If you are running a relatively recent version of Linux, the registry and the
pipeliner are available as a Systemd unit. More details are available in the
administration section.

.. note::

    Both the registry and the pipeliner accept command line arguments;
    run ``pipeliner.py -h`` or ``registry.py -h`` to get a list of them.

Now, your PALM cluster is up and waiting for servers and clients to
appear.

.. important::

    It does not care in which node of your etcd cluster are the registry
    and the pipeliner running, as long as they have access to etcd. To test
    if the node you are on is running etcd correctly, just run ``etcdctl
    cluster-health``.  Only one of each can be running at the same time **for
    the whole cluster**. Fortunately, the
    workload of these two services is moderate, and you won't need to
    cluster them. If one of them crashes, you just have to start them
    again, and the service should recover the previous state, since
    everything is stored in the etcd database.

What is a *PALM cluster* is yet another important definition. A cluster is a
set of PALM servers that are running in the same etcd cluster and are managed
by the same registry and the same pipeliner. If a server is not able to
access the etcd database, it is not part of the cluster. If either the
registry or the pipeliner is not running, the cluster will not work.

Running PALM servers
--------------------

Running a server (assume a server called ``server.py``) is as easy as

.. code-block:: bash

    $> python server.py run

The handler ``run_server`` that has been included in the examples so far does
some magic for you. To list the options to run each server just use the ``-h``
argument.

.. code-block:: bash

    $> python server -h

    usage: server.py [-h] [-d] [-i] [-e ETCD] [-p IP] [-b DB] run

    positional arguments:
      run                   Run the server.

    optional arguments:
      -h, --help            show this help message and exit
      -d, --debug           increase output verbosity to debug level.
      -i, --info            increase output verbosity to info level.
      -e ETCD, --etcd ETCD  Port of the etcd server.
      -p IP, --ip IP        IP address the server has to use.
      -b DB, --db DB        Folder where the cached data will be stored.

Let me shortly explain each one of the arguments:

``--debug``
    Increase the logging level of the servers to *debug* level. Server logs are
    collected at runtime and sent to the registry, so you won't see any
    output from the servers. Remember that PALM is designed for distributed
    systems.

``--info``
    Increase the logging level of the servers to *info* level.

``--etcd``
    The servers must know the port where the http interface of the etcd
    server listens to requests. If you have not modified etcd in any way, you
    can ignore this argument.

``--ip``
    If you run this PALM server in more than one physical servers, the tcp
    stack needs to know the IP of the host where the server is running.

``--db``
    Servers persist data in disk. All the data will be saved in this
    directory in an unreadable form (a leveldb data folder). If you leave
    this folder empty, data will be stored in a new folder in the ``/tmp``
    directory.
