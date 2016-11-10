from __future__ import print_function
import requests
from requests.exceptions import ConnectionError
from jinja2 import Template
from xml.dom.minidom import parseString
import xmltodict
import json
import time
import paramiko
import socket
import logging


__author__ = 'aradford1'


class Schema(object):

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


class ExecTemplate(Schema):

    def __init__(self):
        """

        :type self: object
        """
        Schema.__init__(self)
        self.body = """<request xmlns="urn:cisco:wsma-exec"
                correlator="{{CORRELATOR}}">
               <execCLI maxWait="PT100S" xsd="false" {{FORMAT}}>
                <cmd>{{EXEC_CMD}}</cmd>
               </execCLI> """
        self.template = Template("{0}{1}{2}".
                                 format(self.begin_schema,
                                        self.body,
                                        self.end_schema))


class ConfigTemplate(Schema):

    def __init__(self):
        Schema.__init__(self)
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


class ConfigPersistTemplate(Schema):

    def __init__(self):
        """

        :type self: object
        """
        Schema.__init__(self)
        self.body = """<request xmlns="urn:cisco:wsma-config"
                correlator="{{CORRELATOR}}">
               <configPersist>
               </configPersist>"""
        self.template = Template("{0}{1}{2}".
                                 format(self.begin_schema,
                                        self.body,
                                        self.end_schema))


class WSMAbase(object):
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
        self.count = 1

    def wsma_exec(self, command, format_spec=None):
        '''
        run given command in exec mode, return JSON response
        :param command: to be run in exec mode on device
        :param format_spec: if there is a ODM spec file for the command
        :return: json response
        '''
        correlator = self.build_correlator("exec" + command)
        if format_spec is not None:
            format_text = 'format="%s"' % format_spec
        else:
            format_text = ""
        etmplate = ExecTemplate()
        template_data = etmplate.template.render(EXEC_CMD=command,
                                                 CORRELATOR=correlator,
                                                 FORMAT=format_text,
                                                 Username=self.username,
                                                 Password=self.password)
        logging.debug("Template {0:s}".format(template_data))
        return self._run_and_return(template_data)

    def wsma_exec_text(self, command, format_spec=None):
        '''
        same as wsma_exec, but returns only the text object or
        error message if the command was not successful.
        :param command: to be run in exec mode on device
        :param format_spec: if there is a ODM spec file for the command
        :return CLI output
        '''
        d = self.wsma_exec(command, format_spec)
        try:
            t = d['response']['execLog']['dialogueLog']['received']['text']
        except IndexError as e:
            return 'unknown error'
        if t is not None:
            return t
        else:
            return d['response']['execLog']['errorInfo']['errorMessage']

    def wsma_config(self, command, action_on_fail="stop"):
        '''

        :param command: config block to be applied to the device
        :param action_on_fail, can be "stop", "continue", "rollback"
        :return: json response
        '''
        correlator = self.build_correlator("config")
        fail_str = 'action-on-fail="%s"' % action_on_fail
        self.count = self.count + 1
        etmplate = ConfigTemplate()
        template_data = etmplate.template.render(CONFIG_CMD=command,
                                                 CORRELATOR=correlator,
                                                 ACTION_ON_FAIL=fail_str,
                                                 Username=self.username,
                                                 Password=self.password)
        logging.debug("Template {0:s}".format(template_data))

        return self._run_and_return(template_data)

    def wsma_config_persist(self):
        '''

        :return: json response
        '''
        correlator = self.build_correlator("config-persist")
        etmplate = ConfigPersistTemplate()
        template_data = etmplate.template.render(CORRELATOR=correlator,
                                                 Username=self.username,
                                                 Password=self.password)
        logging.debug("Template {0:s}".format(template_data))
        return self._run_and_return(template_data)

    def build_correlator(self, command):
        '''

        :param command: used to make a unique string to return as a correlator
        :return:
        '''
        result = time.strftime("%H%M%S")
        result += "-%s" % str(self.count)
        result += ''.join(command.split())
        self.count += 1
        return result

    @staticmethod
    def parse_xml(xml_text):
        '''

        :param xml_text: xml to be converted
        :return: json
        '''
        logging.debug("xml: {0:s}".format(xml_text))
        if xml_text is None:
            return {'error': 'xml body is empty'}
        dom = parseString(xml_text)
        response = dom.getElementsByTagName('response')
        if len(response) == 0:
            return {'error': 'no XML "response" received'}
        response_xml = response[0].toprettyxml()
        return xmltodict.parse(response_xml)

    def _run_and_return(self, template_data):
        '''
        needs to be implemented in child
        :param template_data: will be xml format data to be sent in transaction
        :return:
        '''
        pass


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

    def _run_and_return(self, template_data):
        '''

        :param template_data: xml data to be send
        :return: xml_text
        '''
        try:
            logging.info('Trying {}, {}/{}'.format(self.url,
                                                   self.username,
                                                   self.password))
            if not self.verify:
                requests.packages.urllib3.disable_warnings()

            response = requests.post(url=self.url, data=template_data,
                                     auth=(self.username,
                                           self.password),
                                     verify=self.verify,
                                     timeout=60)
            logging.debug(response.content)
        except ConnectionError as conn_err:
            logging.error("Connection Error {0:s}".format(conn_err))
            return {'error': "404 bad connection"}
        # this needs to be response.content,
        # otherwise generates unicode string error
        xml_text = response.content.decode("utf-8")
        logging.debug("GOT{0:s}DONE".format(xml_text))
        if "401 Unauthorized" in xml_text:
            return {"error": "401 Unauthorized"}
        return self.parse_xml(xml_text)


EOM = "]]>]]>"
BUFSIZ = 16384


class WSMA_SSH(WSMAbase):
    '''
    this is the SSH version of transport
    '''

    def __init__(self, host, username, password, port=22):
        super(WSMA_SSH, self).__init__(host, username, password, port)
        self.t = None
        self.cmd_channel = None

    def connect(self):
        # Socket connection to remote host
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        self.t = paramiko.Transport(sock)
        try:
            logging.info("connect as %s/%s", self.username, self.password)
            self.t.connect(username=self.username, password=self.password)
        except paramiko.AuthenticationException:
            logging.error("SSH Authentication failed.")
            return None
        # Start a wsma channel
        self.cmd_channel = self.t.open_session()
        self.cmd_channel.set_name("wsma")
        self.cmd_channel.invoke_subsystem('wsma')
        # should we look for the "wsma-hello" message?
        hello = self.recv()
        idx = hello.find("wsma-hello")

        if idx == -1:
            logging.error("No wsma-hello from host")
            return None

    def send(self, buf):
        logging.debug("Sending %s", buf)
        self.cmd_channel.sendall(buf)
        self.cmd_channel.sendall(EOM)

    def recv(self):
        bytes = ""
        while len(bytes) < 6:
            x = self.cmd_channel.recv(BUFSIZ)
            if x == "":
                return bytes
            bytes += x
        idx = bytes.find("]]>]]>")
        if idx > -1:
            return bytes[:idx]

    def close(self):
        # Cleanup
        self.cmd_channel.close()
        self.t.close()

    def _run_and_return(self, template_data):
        # need to check return code
        self.connect()

        self.send(template_data)
        response = self.recv()
        self.close()
        logging.debug("GOT{0:s}DONE".format(response))
        return self.parse_xml(response)


if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    #
    # Get who to talk to and username and password
    #
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Provide device parameters:')
    parser.add_argument('--host', type=str, required=True,
                        help="The device IP or DN")
    parser.add_argument('-u', '--username', type=str, default='cisco',
                        help="Username for device")
    parser.add_argument('-p', '--password', type=str, default='cisco',
                        help="Password for specified user")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Enable verbose debugging output.")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    #
    # Create the WSMA utility
    #
    wsma = WSMA(args.host, args.username, args.password)

    #
    # Try some simple tests. Not currently handling error conditions
    # like a failure to connect to the device.
    #
    print(json.dumps(wsma.wsma_config("interface Loopback99"), indent=4))
    print(json.dumps(wsma.wsma_config("no interface Loopback99"), indent=4))

    #
    # Variety of show commands
    #

    #
    # Exec commands that use parsing to structured data on router or
    # switch. Not recommended
    #
    print(json.dumps(wsma.wsma_exec("show ip int br", format_spec="builtin"), indent=4))
    print(json.dumps(wsma.wsma_exec("show ip int br", format_spec=""), indent=4))

    #
    # Show IP interfaces, normal
    #
    print(json.dumps(wsma.wsma_exec("show ip int br"), indent=4))

    #
    # Pick out the OSPF routing process config only
    #
    print(json.dumps(wsma.wsma_exec("show running-config | sec router ospf"), indent=4))

    #
    # Look at IP routes and the IP routes summary
    #
    print(json.dumps(wsma.wsma_exec("show ip route"), indent=4))
    print(json.dumps(wsma.wsma_exec("show ip route summary"), indent=4))

    #
    # Configure and deconfigure a loopback interface
    #
    print(json.dumps(wsma.wsma_config("interface Loopback999"), indent=4))
    print(json.dumps(wsma.wsma_config("no interface Loopback999"), indent=4))

    #
    # Negative tests, one for exec, one for config.
    #
    print(json.dumps(wsma.wsma_exec("show ip intbr"), indent=4))
    print(json.dumps(wsma.wsma_config("nonsense command"), indent=4))
