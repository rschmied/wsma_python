# -*- coding: utf-8 -*-

"""
This defines the base class for the WSMA Python module.
"""

from abc import ABCMeta, abstractmethod
from jinja2 import Template
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError
import xmltodict
import json
import time
import logging


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
              <wsse:Security xmlns:wsse="http://schemas.xmlsoap.org/ws/2002/04/secext" SOAP:mustUnderstand="false">
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
               <execCLI maxWait="PT{{TIMEOUT}}S" xsd="false" {{FORMAT}}>
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


class Base(object):
    '''The base class for all WSMA transports.

    Provides the groundwork for specified transports.
    WSMA defines the following transports:

    - SSH
    - HTTP / HTTPS
    - TLS

    this is the WSMA :class:`Base <Base>` class

    :param host:  hostname of the WSMA server
    :param username: username to use
    :param password: password for the username
    :param port: port to connect to
    :param timeout: timeout for transport
    '''

    __metaclass__ = ABCMeta

    def __init__(self, host, username, password, port, timeout=60):
        super(Base, self).__init__()

        if not host:
            raise ValueError("host argument may not be empty")

        self.timeout = timeout
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
        '''Test the connection, does it make sense to continue?
        it is assumed that

        1) wsma is configured on the device (how could we connect otherwise?)
        2) this is a priv-lvl-1 command
        3) this command is platform independent for platforms supporting WSMA

        an alternative would be "show version"

        :rtype: bool
        '''
        return self.execCLI("show wsma id")

    def _buildCorrelator(self, command):
        '''Build a correlator for each command. Consists of
        - command to be sent -and-
        - timestamp

        :param command: used to make a unique string to return as a correlator
        :rtype: str
        '''
        result = time.strftime("%H%M%S")
        result += "-%s" % str(self._count)
        result += ''.join(command.split())
        self._count += 1
        return result

    def _process(self, data):
        '''Process the given data dict and populate instance vars:
        - success: was the call successful (bool)
        - output: holds CLI output (e.g. for show commands), (string)
                  if the call wass successful.
                  it holds the error message (typos, config and exec)
                  if not successful
        - data: holds the raw dict from the device

        :param data: dictionary with response data
        :rtype: bool
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
            return False

        # exec mode?
        if self.data['response']['@xmlns'] == "urn:cisco:wsma-exec":
            if self.success:
                try:
                    t = self.data['response']['execLog'][
                        'dialogueLog']['received']['text']
                except KeyError:
                    t = None
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
        '''Needs to be overwritten in subclass, it should process the
        'template_data' by sending it using the selected transport.
        Then pass the received response data through _process(),
        returning the result from _process().

        :param template_data: XML string to be sent in transaction
        :rtype: bool
        '''
        pass

    @abstractmethod
    def connect(self):
        '''Connects to the WSMA host via a specific transport.
        The specific implementation has to be provided by
        the subclass. tls, ssh and http(s) are usable in IOS.
        '''
        logging.info("connect to {} as {}/{}".format(self.url,
                                                     self.username,
                                                     self.password))

    @abstractmethod
    def disconnect(self):
        '''Disconnects the transport
        '''
        logging.info("disconnect from {}".format(self.url))

    @property
    def odmFormatResult(self):
        '''When using format specifications (e.g. structured data
        instead of unstructured CLI output) then this property
        holds the structured data as an object.
        '''
        try:
            return self.data['response']['execLog']['dialogueLog']['received']['tree']
        except KeyError:
            return None

    def execCLI(self, command, format_spec=None):
        '''Run given command in exec mode, return JSON response. The
        On success, self.output and self.success will be updated.

        If format_spec is given (and valid), odmFormatResult will
        contain the dictionary with the result data.

        :param command: command string to be run in exec mode on device
        :param format_spec: if there is a ODM spec file for the command
        :rtype: bool
        '''
        correlator = self._buildCorrelator("exec" + command)
        if format_spec is not None:
            format_text = 'format="%s"' % format_spec
        else:
            format_text = ""
        etmplate = _ExecTemplate()
        template_data = etmplate.template.render(EXEC_CMD=command,
                                                 TIMEOUT=self.timeout,
                                                 CORRELATOR=correlator,
                                                 FORMAT=format_text,
                                                 Username=self.username,
                                                 Password=self.password)
        logging.debug("Template {}".format(template_data))
        return self.communicate(template_data)

    def config(self, command, action_on_fail="stop"):
        '''Execute given commands in configuration mode.
        On success, self.output and self.success will be updated.

        :param command: config block to be applied to the device
        :param action_on_fail, can be "stop", "continue", "rollback"
        :rtype: bool
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
        '''Makes configuration changes persistent.

        :rtype: bool
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
        '''Parses given XML string and returns the 'response' child within the
        XML tree. If no response is found, the SOAP 'Envelope' is returned.

        If an empty string is used or an error occurs during parsing then
        dict(error='some error string') is returned.

        This still assumes that IF an XML string is passed into
        this function then it should have a valid SOAP Envelope.

        :param xml_text: XML string to be converted
        :rtype: dict
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
        try:
            dom = parseString(xml_text)
        except ExpatError as e:
            return {'error': '%s' % e}

        logging.debug("XML tree:{}".format(dom.childNodes[-1].toprettyxml()))

        response = dom.getElementsByTagName('response')
        if len(response) > 0:
            return xmltodict.parse(response[0].toxml())

        return xmltodict.parse(
            dom.getElementsByTagNameNS(
                "http://schemas.xmlsoap.org/soap/envelope/",
                "Envelope")[0].toxml())
