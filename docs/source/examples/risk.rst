Worked example. Montecarlo simulation.
======================================

.. math::

   r_{i+1} = r_i + \sigma \sqrt{T} \epsilon_i


First step. Plan your messages.
-------------------------------

This is a distributed system, therefore it is essential to think and
rethink how you will distribute your data. The bigger the message, the
lower the performance. The more messages you send, the lower the
performance.

.. code-block:: none

  message SimulationData {
    repeated double times = 1;
    required double sigma = 2;
    required int64  simulations = 3;
  }
  
