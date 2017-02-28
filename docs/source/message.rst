The PALM message
================

Every single server and process in PALM, and of course pylm, uses the
following
`Google's protocol buffers message <https://developers.google.com/protocol-buffers/>`_.
message.

.. literalinclude:: ../../pylm/parts/messages.proto
    :language: protobuf
    :linenos:

If you don't want to dive within the internals of the servers, it is likely
that you don't have to even know about it, but it is relevant if you want to
understand how servers (and their parts) communicate with each other. As you
see, the server has a set of fields, just like a tuple. Each one is used for
a different purpose:

:pipeline: This is an unique identifier of the stream of messages that is
    sent from the client. It is necessary for the servers to be able to
    handle multiple streams of messages at the same time.

:client: An unique ID of the client that initiated the stream.

:stage: Counter of the step within the stream that the message is going
    through. Every client initiates this value to 0. Every time that the
    message goes through a server, this counter is incremented.

:function: A string with a server.method identifier, or a series of them
    separated by spaces. These are the functions that have to be called at
    each step of the pipeline. Of course, this variable needs *stage* to be
    useful if there are more than one steps to go through.

:cache: This is an utility variable used for various purposes. When the
    client communicates with the cache of the servers, this variable brings
    the key for the key-value store. It is also used internally by some
    servers to keep track of messages that are being circulated by their
    internal parts. You can mostly ignore this field, and use it only when
    you know what you are doing.

:payload: The actual data carried by the message. It is usually a bunch of
    bits that you have to deserialize.

Again, if you use the simplest parts of the high-level API, you can probably
ignore all of this, but if you want to play with the stream of messages, or
you want to play with the internal of the servers, you need to get
comfortable with all those fields.