.. _hub:

The Hub server
==============

The hub server is a master that can be connected like a pipeline. It
therefore needs some more information to be added to a cluster. Instead of
pulling from clients, it subscribes to a stream of messages coming from a
master or a server. This is the reason why you have a sub connection instead
of a pull service, and you have to take into account when configuring it.

There is yet another change respect to a master server, the *previous*
parameter. If you don't want to play dirty tricks to the message stream, i.e.
routing a message to a particular subscribed server, it's just the name of
the previous server the hub is subscribed to.

Maybe the simplest stream of messages involving a hub is the following.

.. only:: html

    .. figure:: _images/server_hub.png
        :align: center

.. only:: latex

    .. figure:: _images/server_hub.pdf
        :align: center
        :scale: 60

You can see an example how the output of a server can be pipelined to a hub
in the example :ref:`server-hub`.