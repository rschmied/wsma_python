# -*- coding: utf-8 -*-

""" WSMA -- HTTP transport """

from wsma.base import Base
import requests
from requests.exceptions import ConnectionError
from ssl import SSLError
import logging


__author__ = 'aradford1'


class HTTP(Base):
    '''
    This is the HTTP(s) version of transport
    '''

    def __init__(self, host, username, password, port=443, tls=True, verify=True):
        super(HTTP, self).__init__(host, username, password, port)
        fmt = dict(prot='https' if tls else 'http',
                   host=self.host, port=self.port)
        # in Python3, should use .format_map(fmt)
        self.url = "{prot}://{host}:{port}/wsma".format(**fmt)
        self.verify = verify if tls else False

    def connect(self):
        super(HTTP, self).connect()
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
                                   timeout=self.timeout)
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
