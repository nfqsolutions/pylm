from pylm_ng.components.connections import PushBypassConnection
import logging


class LogHandler(PushBypassConnection):
    def __init__(self, name, listen_address):
        super(LogHandler, self).__init__(name, listen_address)

    def write(self, message):
        """
        Write method to behave like a file
        :param message: Message to be sent
        :return:
        """
        self.send(message_data=message.encode('utf-8'))


PylmLogFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

