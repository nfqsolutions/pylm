.. _standalone:

Standalone servers
==================

An example of the simplest standalone server was presented in the :ref:`introduction`. A single server running
in a single process may be useful, but there are a million alternatives to pylm for that. The real usefulness
of pylm arrives when the workload is so large that a single server is not capable of handling it. Here we introduce
parallelism for the first time with the parallel standalone server.