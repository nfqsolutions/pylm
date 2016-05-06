PALM
====
 
PALM is a library to create clusters of high-performance micro-services with simple and reusable components.
In PALM, all servers are equal, and they have the same capabilities: a RPC mechanism, a cache, logging,
performance counters... PALM also provides the required infrastructure to deploy, configure and monitor the cluster.

![](./docs/source/_images/cluster.svg)
 
It also adds a connection model for those clusters: a pipeline. A pipeline is a sequence of servers receiving
messages and sending some result to the following. A Job is a pipeline definition and a set of messages that
start the computation. The item that submits a job is a PALM client. This means that a pipeline is only part
of a job specification, and it is not hardcoded in the configuration of the cluster. Again, all servers are equal.

![](./docs/source/_images/pipeline.svg)

The magic of PALM is half hidden within the servers. There are five kind of server templates, that you must
subclass to implement your business logic. Some of them are designed to be a step in the pipeline, while others
are able to perform a parallel multiple-step reduction based on the data of the message stream, or a self-balancing
ventilator-sink parallel computation. In consequence, PALM can be used to build custom applications with dynamic
parallelism, with some of the nice features expected in high performance applications: efficient messaging,
memory efficiency, load balancing and so on.

Pylm
----

Pylm is the python implementation of the PALM servers, and provides the fundamental infrastructure to run
a PALM cluster. You can check the documentation of PALM and pylm [here](https://pythonhosted.org/pylm/). 
Pylm is also the reference implementation of all the components. A second
complete implementation of the PALM servers is also being implemented in Java, and it is called 
[palm-java](https://bitbucket.org/ekergy/palm-java).