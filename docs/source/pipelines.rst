What is a pipeline and why they are useful.
===========================================

The pipeline at the beginning of this document was pictured in a slightly
misleading way. The figure emphasizes the motto of *all servers are equal*
while the stream of messages is not properly emphasized.  We could represent
the same job the following way.

.. only:: html

    .. figure:: _images/job_example.png
        :align: center

.. only:: latex

    .. figure:: _images/job_example.pdf
        :align: center
        :scale: 60


Again, the client starts a stream of messages. Each server reacts to a
message on its own particular way, generating more messages. Finally, the
stream of messages is consumed somehow or lost forever (maybe Server B has
some persistence, and it is able to save the information carried by each
message).

.. important::

    Note that Server B appears twice in the pipeline. You do not have to run
    Server B twice, it is just called twice.

This paradigm can be also described as *chained RPC* where the server,
instead of responding the original caller, they send a RPC to yet another
server.

Parallelism
-----------

Every server runs in a different process. This means that the pipeline itself
is some sort of task-based parallelism. I know what you are thinking. If one
of those servers, say Server C, is doing a very heavy task, the whole
message stream will be slowed down by that server. The performance of the
complete pipeline will be the performance of the slowest server. Of course,
we have anticipated that possibility.

The way each server has been represented hides an important piece of
complexity. Some of those servers hide a master-slave pattern of parallel
computation. In fact, you can choose between three of them, and each one
implements a particular kind of variant of that pattern.

Say that Server C must execute a particularly heavy task, and we do not want
it to be a bottleneck. If the task is CPU intensive, we can introduce a
ventilator-sink parallel pipeline within the Server C as follows.

.. only:: html

    .. figure:: _images/butterfly_example.png
        :align: center

.. only:: latex

    .. figure:: _images/butterfly_example.pdf
        :align: center
        :scale: 60

If Server C is blocking the pipeline, now the pipeline is about six times
faster.

You are probably wondering how much one has to change the code to turn a
serial server into a parallel server. The answer is that it depends. If you
just want to parallelize the computation of a function without any kind of
process synchronization, namely a reduction, the actual answer is not much.
Assume that you had implemented a serial server inheriting from
``RegisteredServer``

.. code-block:: python

    from pylm.components import RegisteredServer, run_server

    class SomeServer(RegisteredServer):
        """Serial version of SomeServer"""
        def business_logic(self, message):
            payload = deserialize(message)
            value = very_long_computation(payload)
            return serialize(value)

    if __name__ == '__main__':
        run_server(SomeServer, 'my_server', ['business_logic'])

The parallel version would be implemented like this

.. code-block:: python
    :emphasize-lines: 1, 3

    from pylm.components import ButterflyServer, run_server

    class SomeServer(ButterflyServer):
        """Serial version of SomeServer"""
        def business_logic(self, message):
            payload = deserialize(message)
            value = very_long_computation(payload)
            return serialize(value)

    if __name__ == '__main__':
        run_server(SomeServer, 'my_server', ['business_logic'])

That's it. You just inherit from a different base class.

Well. To be more precise, that is the only way in which you must change your
**code**. If you want your pipeline to actually run in parallel with 6
workers, you will have to launch **7 instances** of SomeServer. One of the
instances will work as the leader (the source and the sink) while the other
6 will be the workers. The ensemble of instances will deal with the internal
messaging, and you should not care about that at all.

There are other two variants of servers that hide some level of parallelism:
``ReduceServer`` and ``ScatterGatherServer``. You will learn more about them
in the examples section.

Composability
-------------

Pipelines by itself are a way of composing several features into a
single, integrated tool. The message stream is successively transformed by
each server until the final state is achieved. From a syntactic point of view
. Composability is important to implement a structured solution to a non
trivial problem. The implementation can be split in a series of smaller
servers that are easier to implement and to maintain.

Think about `Conway's law <https://en.wikipedia.org/wiki/Conway%27s_law>`_:
if there are 5 employees, there will be 4 modules, because one of them will
be the manager.  Servers are a natural way of organizing work, and messages
are a contract between two servers, which allow to standardize the interface
between developers too.

Reusability
-----------

PALM servers are called servers because that is what they are. They run as
separate processes, even the workers of parallel servers. They produce logs,
they are completely autonomous and they have a completely defined behavior,
since they only listen to messages that can be deserialized.

A PALM server can be reused in any PALM cluster, in consequence, servers have
to be implemented only once.

Heterogeneity
-------------

Some servers will require persistence, others will require a specific kind of
CPU, while others may need some mechanism of data acquisition. All servers,
even the workers, have to be launched by a scheduler. In fact, servers can be
easily configured to become systemd units. PALM handles some aspects of
process management (monitoring and logging), but does not require a
particular way of launching the services. You can use Fleet, Kubernetes, or
anything else.

If you scheduler is powerful enough, you will be able to run each server on
the most suitable hardware possible.

What PALM cannot do
-------------------

The design of PALM is based on a thoughtful study of the requirements of
applications developed at NFQ Risk Solutions. None of them ever does a
map-reduce operation. They usually do a map, sometimes a reduce, but never a
shuffle. PALM ignores the shuffle operation because it simplifies the design
of the library. A shuffle is an all-to-all operation, where each node talks
to each one of its peers, and it would be hard to implement while keeping the
notion of a pipeline at the same time.  PALM would be larger and more complex
with a pipelined shuffle.

Another operation that is not supported by PALM is the merging of two
pipelines. A pipeline can be in fact split in two with a server called
``SourceServer``, which is relatively simple to use, and it was also easy to
implement. But merging two pipelines requires knowing what are the
dependencies between messages in the two message streams. This is usually not
a simple rule, and that is the reason why this operation is not supported.
However, if there is no dependency between the two streams, they can be
merged by saving all the messages of one of them in the cache of a target
server. We will cover this case in an example.



