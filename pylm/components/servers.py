from pylm.components.messages_pb2 import PalmMessage


class BaseMaster(object):
    @staticmethod
    def change_payload(message: bytes, new_payload: bytes) -> bytes:
        """
        Change the payload of the message

        :param message: The binary message to be processed
        :param new_payload: The new binary payload
        :return: Serialized message with the new payload
        """
        palm_message = PalmMessage()
        palm_message.ParseFromString(message)
        palm_message.payload = new_payload
        return palm_message.SerializeToString()

    @staticmethod
    def change_call(message: bytes, next_server: str, next_call: str) -> bytes:
        """
        Assign a call for the next server

        :param message: The binary message to be processed
        :param next_server: The name of the next server
        :param next_call: The name of the function to be called
        :return: Serialized message with the new call
        """
        call = '.'.join([next_server, next_call])
        palm_message = PalmMessage()
        palm_message.ParseFromString(message)
        palm_message.function = call
        return palm_message.SerializeToString()

    def scatter(self, message: bytes):
        """
        Scatter function for inbound messages

        :param message: Binary message
        :return: Yield none, one or multiple binary messages
        """
        yield message

    def gather(self, message: bytes):
        """
        Gather function for outbound messages

        :param message: Binary message
        :return: Yield none, one or multiple binary messages
        """
        yield message
