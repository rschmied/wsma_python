# -*- coding: utf-8 -*-

""" WSMA SSH transport """

from wsma.base import Base
import paramiko
import socket
import logging


class SSH(Base):
    '''This is the SSH version of transport.
    It returns a :class:`SSH <SSH>` object

    :param host: FQDN or IP (str)
    :param username: username (str)
    :param password: password for user (str)
    :param port: which port to connec to? (int)
    :param \*\*kwargs: Optional arguments that ``.Base`` takes.
    '''

    EOM = "]]>]]>"
    BUFSIZ = 16384

    def __init__(self, host, username, password, port=22, **kwargs):
        super(SSH, self).__init__(host, username, password, port, **kwargs)
        self.session = None
        self._cmd_channel = None
        fmt = dict(prot='ssh', host=self.host, port=self.port)
        # in Python3, should use .format_map(fmt)
        self.url = "{prot}://{host}:{port}".format(**fmt)

    def _send(self, buf):
        logging.debug("Sending %s", buf)
        self._cmd_channel.sendall(buf)
        self._cmd_channel.sendall(self.EOM)

    def _recv(self):
        bytes = u""
        while len(bytes) < len(self.EOM):
            x = self._cmd_channel.recv(self.BUFSIZ).decode('utf-8')
            if x == "":
                return bytes
            bytes += x
        idx = bytes.find(self.EOM)
        if idx > -1:
            return bytes[:idx]

    def connect(self):
        '''Connect to the WSMA service using SSH
        '''
        super(SSH, self).connect()

        # Socket connection to remote host
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        self.session = paramiko.Transport(sock)
        try:
            self.session.connect(username=self.username,
                                 password=self.password)
        except paramiko.AuthenticationException:
            logging.error("SSH Authentication failed.")
            return None

        # Start a wsma channel
        self._cmd_channel = self.session.open_session()
        self._cmd_channel.set_name("wsma")
        self._cmd_channel.invoke_subsystem('wsma')

        # should we look for the "wsma-hello" message?
        hello = self._recv()
        idx = hello.find("wsma-hello")

        if idx == -1:
            logging.error("No wsma-hello from host")
            return None

    def disconnect(self):
        '''Disconnect the SSH session
        '''
        super(SSH, self).disconnect()
        self._cmd_channel.close()
        self.session.close()

    def communicate(self, template_data):
        '''Communicate with the WSMA service using SSH
        '''
        self._send(template_data)
        response = self._recv()
        logging.debug("DATA: %s", response)
        return self._process(self.parseXML(response))
