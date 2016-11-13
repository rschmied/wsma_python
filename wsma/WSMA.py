# -*- coding: utf-8 -*-

"""
WSMA 

The Web Services Management Agent (WSMA) defines a mechanism through which a
network device can be managed, configuration data information can be
retrieved, and new configuration data can be uploaded and manipulated. WSMA
uses Extensible Markup Language (XML)-based data encoding, that is transported
by the Simple Object Access Protocol (SOAP), for the configuration data and
protocol messages. 

Reference:
http://www.cisco.com/c/en/us/td/docs/ios/netmgmt/configuration/guide/Convert/WSMA/nm_cfg_wsma.html

"""


from __future__ import print_function
from abc import ABCMeta, abstractmethod
import requests
from requests.exceptions import ConnectionError
from ssl import SSLError
from jinja2 import Template
from xml.dom.minidom import parseString
import xmltodict
import json
import time
import paramiko
import socket
import logging


__author__ = 'aradford1'


class _Schema(object):

    def __init__(self):
        """

        :rtype : basestring
        """
        self.begin_schema = """<?xml version="1.0" encoding="UTF-8"?>
            <SOAP:Envelope xmlns:SOAP="http://schemas.xmlsoap.org/soap/envelope/"
            xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"
            xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <SOAP:Header>
              <wsse:Security xmlns:wsse="http://schemas.xmlsoap.org/ws/2002/04/secext"  SOAP:mustUnderstand="false">
                  <wsse:UsernameToken>
                     <wsse:Username>{{Username}}</wsse:Username>
                     <wsse:Password>{{Password}}</wsse:Password>
                   </wsse:UsernameToken>
            </wsse:Security>
            </SOAP:Header>
             <SOAP:Body> """

        self.end_schema = """  </request>
                 </SOAP:Body>
                </SOAP:Envelope>"""


class _ExecTemplate(_Schema):

    def __init__(self):
        """

        :type self: object
        """
        _Schema.__init__(self)
        self.body = """<request xmlns="urn:cisco:wsma-exec"
                correlator="{{CORRELATOR}}">
               <execCLI maxWait="PT100S" xsd="false" {{FORMAT}}>
                <cmd>{{EXEC_CMD}}</cmd>
               </execCLI> """
        self.template = Template("{0}{1}{2}".
                                 format(self.begin_schema,
                                        self.body,
                                        self.end_schema))


class _ConfigTemplate(_Schema):

    def __init__(self):
        _Schema.__init__(self)
        self.body = """<request xmlns="urn:cisco:wsma-config"
                correlator="{{CORRELATOR}}">
              <configApply details="all" {{ACTION_ON_FAIL}}>
               <config-data>
                <cli-config-data-block>{{CONFIG_CMD}}</cli-config-data-block>
             </config-data>
             </configApply>"""
        self.template = Template("{0}{1}{2}".
                                 format(self.begin_schema,
                                        self.body,
                                        self.end_schema))


class _ConfigPersistTemplate(_Schema):

    def __init__(self):
        """

        :type self: object
        """
        _Schema.__init__(self)
        self.body = """<request xmlns="urn:cisco:wsma-config"
                correlator="{{CORRELATOR}}">
               <configPersist>
               </configPersist>"""
        self.template = Template("{0}{1}{2}".
                                 format(self.begin_schema,
                                        self.body,
                                        self.end_schema))


class WSMAbase(object, metaclass=ABCMeta):
    '''
    :param host:  hostname of the WSMA server
    :param username: username to connect
    :param password: password for user account
    '''

    def __init__(self, host, username, password, port):
        if not host:
            raise ValueError("host argument may not be empty")

        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.success = False
        self.output = ''
        self.data = None

        # session holds the transport session
        self._session = None
        # count is used for the correlator over
        # the existence of the session
        self._count = 0

    def __enter__(self):
        logging.debug('WITH/AS connect session')
        self.connect()
        return self if self._ping() else None

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.debug('WITH/AS disconnect session')
        self.disconnect()

    def _ping(self):
        """
        test the connection, does it make sense to continue?
        it is assumed that 
        1) wsma is configured on the device (how could we connect otherwise?)
        2) this is a priv-lvl-1 command
        3) this command is platform independent for platforms supporting WSMA

        an alternative would be "show version"

        :returns: Bool
        """
        return self.execCLI("show wsma id")

    def _buildCorrelator(self, command):
        '''

        :param command: used to make a unique string to return as a correlator
        :return:
        '''
        result = time.strftime("%H%M%S")
        result += "-%s" % str(self._count)
        result += ''.join(command.split())
        self._count += 1
        return result

    def _process(self, data):
        '''
        the following class variables get populated:
        - success: was the call successful (bool)
        - output: holds CLI output (e.g. for show commands), (string)
                  if the call wass successful.
                  it holds the error message (typos, config and exec)
                  if not successful
        - data: holds the raw dict (as returned from the device)

        :process CLI output
        :updates self.success, self.output and self.data
        :returns Bool for success 
        '''
        self.success = False
        self.output = ''
        self.data = data

        if self.data is None:
            return False

        logging.info("JSON data: %s", json.dumps(self.data, indent=4))

        # was it successful?
        try:
            self.success = bool(int(self.data['response']['@success']))
        except KeyError:
            self.output = 'unknown error / key error'

        # exec mode?
        if self.data['response']['@xmlns'] == "urn:cisco:wsma-exec":
            if self.success:
                t = self.data['response']['execLog'][
                    'dialogueLog']['received']['text']
                t = '' if t is None else t
                self.output = t
                return True

            if not self.success:
                e = self.data['response']['execLog'][
                    'errorInfo']['errorMessage']
                self.output = e
                return False

        # config mode?
        if self.data['response']['@xmlns'] == "urn:cisco:wsma-config":
            if self.success:
                t = 'config mode / not applicable'
                self.output = t
                return True

            if not self.success:
                re = self.data['response']['resultEntry']
                # multi line config input returns list
                if type(re) is list:
                    results = re
                else:
                    results = list()
                    results.append(re)

                # look for first failed element
                for line in results:
                    if line.get('failure'):
                        self.output = line.get('text')
                        break
                return False

        # catch all
        return False

    @abstractmethod
    def communicate(self, template_data):
        '''
        Needs to be overwritten in subclass, it should process the
        'template_data', pass the resulting data through _process()
        and then return the data to the caller.

        :param template_data: will be xml format data to be sent in transaction
        :return:
        '''
        pass

    @abstractmethod
    def connect(self):
        '''
        connects to the WSMA host via a specific transport.
        The specific implementation has to be provided by
        the subclass. tls, ssh and http(s) are usable in IOS.
        '''
        logging.info("connect to {} as {}/{}".format(self.url,
                                                     self.username, self.password))

    @abstractmethod
    def disconnect(self):
        logging.info("disconnect from {}".format(self.url))

    def execCLI(self, command, format_spec=None):
        '''
        run given command in exec mode, return JSON response
        :param command: to be run in exec mode on device
        :param format_spec: if there is a ODM spec file for the command
        :return: Bool, updates result, text and success
        '''
        correlator = self._buildCorrelator("exec" + command)
        if format_spec is not None:
            format_text = 'format="%s"' % format_spec
        else:
            format_text = ""
        etmplate = _ExecTemplate()
        template_data = etmplate.template.render(EXEC_CMD=command,
                                                 CORRELATOR=correlator,
                                                 FORMAT=format_text,
                                                 Username=self.username,
                                                 Password=self.password)
        logging.debug("Template {0:s}".format(template_data))
        return self.communicate(template_data)

    def config(self, command, action_on_fail="stop"):
        '''

        :param command: config block to be applied to the device
        :param action_on_fail, can be "stop", "continue", "rollback"
        :return: Bool, updates result, text and success
        '''
        correlator = self._buildCorrelator("config")
        fail_str = 'action-on-fail="%s"' % action_on_fail
        self._count += 1
        etmplate = _ConfigTemplate()
        template_data = etmplate.template.render(CONFIG_CMD=command,
                                                 CORRELATOR=correlator,
                                                 ACTION_ON_FAIL=fail_str,
                                                 Username=self.username,
                                                 Password=self.password)
        logging.debug("Template {0:s}".format(template_data))
        return self.communicate(template_data)

    def configPersist(self):
        '''

        :return: Bool, updates result, text and success
        '''
        correlator = self._buildCorrelator("config-persist")
        etmplate = _ConfigPersistTemplate()
        template_data = etmplate.template.render(CORRELATOR=correlator,
                                                 Username=self.username,
                                                 Password=self.password)
        logging.debug("Template {0:s}".format(template_data))
        return self.communicate(template_data)

    @staticmethod
    def parseXML(xml_text):
        '''

        :param xml_text: xml to be converted
        :return: json
        '''

        if xml_text is None:
            return {'error': 'XML body is empty'}

        """
        from lxml import etree
        etree.register_namespace("SOAP", "http://schemas.xmlsoap.org/soap/envelope/")
        element = etree.fromstring(xml_text.encode('utf-8'))
        print('#' * 40)
        print(etree.tostring(element, pretty_print=True).decode('utf-8'))
        print(json.dumps(xmltodict.parse(xml_text), indent=4))
        """

        logging.debug("XML string: {}".format(xml_text))
        dom = parseString(xml_text)
        logging.debug("XML tree:{}".format(dom.childNodes[-1].toprettyxml()))

        response = dom.getElementsByTagName('response')
        if len(response) > 0:
            return xmltodict.parse(response[0].toxml())

        return xmltodict.parse(
            dom.getElementsByTagNameNS(
                "http://schemas.xmlsoap.org/soap/envelope/", 
                "Envelope")[0].toxml())


class WSMA(WSMAbase):
    '''
    This is the HTTP(s) version of transport
    '''

    def __init__(self, host, username, password, port=443, tls=True, verify=True):
        super(WSMA, self).__init__(host, username, password, port)
        fmt = dict(prot='https' if tls else 'http',
                   host=self.host, port=self.port)
        # in Python3, should use .format_map(fmt)
        self.url = "{prot}://{host}:{port}/wsma".format(**fmt)
        self.verify = verify if tls else False

    def connect(self):
        super(WSMA, self).connect()
        self._session = requests.Session()
        self._session.auth = (self.username, self.password)
        if not self.verify:
            requests.packages.urllib3.disable_warnings()

    def disconnect(self):
        self._session.close()

    def communicate(self, template_data):
        '''

        :param template_data: xml data to be send
        :return: json response
        '''
        try:
            r = self._session.post(url=self.url, data=template_data,
                                   verify=self.verify,
                                   timeout=60)
            logging.debug("DATA: %s", r.text)
        except (ConnectionError, SSLError) as e:
            logging.error("Connection Error {}".format(e))
            self.success = False
            self.output = e
            return False

        logging.info("status %s", str(r.status_code))
        if not r.ok:
            self.success = False
            self.output = r.text
            return False

        # this needs to be response.content,
        # otherwise generates unicode string error
        xml_text = r.content.decode("utf-8")
        return self._process(self.parseXML(xml_text))


class WSMA_SSH(WSMAbase):
    '''
    this is the SSH version of transport
    '''

    EOM = "]]>]]>"
    BUFSIZ = 16384

    def __init__(self, host, username, password, port=22):
        super(WSMA_SSH, self).__init__(host, username, password, port)
        self.session = None
        self._cmd_channel = None
        fmt = dict(prot='ssh', host=self.host, port=self.port)
        # in Python3, should use .format_map(fmt)
        self.url = "{prot}://{host}:{port}/wsma".format(**fmt)

    def connect(self):
        super(WSMAbase).connect()

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
        hello = self.recv()
        idx = hello.find("wsma-hello")

        if idx == -1:
            logging.error("No wsma-hello from host")
            return None

    def _send(self, buf):
        logging.debug("Sending %s", buf)
        self._cmd_channel.sendall(buf)
        self._cmd_channel.sendall(EOM)

    def _recv(self):
        bytes = ""
        while len(bytes) < len(EOM):
            x = self._cmd_channel.recv(BUFSIZ)
            if x == "":
                return bytes
            bytes += x
        idx = bytes.find(EOM)
        if idx > -1:
            return bytes[:idx]

    def disconnect(self):
        # Cleanup
        self._cmd_channel.close()
        self.session.close()

    def communicate(self, template_data):
        # need to check return code
        self._send(template_data)
        response = self._recv()
        logging.debug("DATA: %s", response)
        return self._process(self.parseXML(response))
