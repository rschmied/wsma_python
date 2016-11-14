#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" execute a few show and config commands """

from __future__ import print_function
import wsma
from argparse import ArgumentParser
import logging
import readline
import sys

def main(argv):

    # enable basic logging
    logging.basicConfig()

    # Get who to talk to and username and password
    parser = ArgumentParser(description='Provide device parameters:')
    parser.add_argument('host', type=str,
                        help="The device IP or DN")
    parser.add_argument('username', type=str, default='cisco', nargs='?',
                        help="Username for device, default is 'cisco'")
    parser.add_argument('password', type=str, default='cisco', nargs='?',
                        help="Password for specified user, default is 'cisco'")
    parser.add_argument('-p', '--port', type=int, default=80,
                        help="Port of WSMA agent.")
    parser.add_argument('-n', '--notls', default=False, action='store_true',
                        help="Don't use TLS")
    parser.add_argument('-l', '--loglevel', type=int, choices=range(0, 5),
                        default=2, help="loglevel, 0-4 (default is 2)")
    args = parser.parse_args()

    # setup logging
    logging.getLogger().setLevel(logging.CRITICAL - (args.loglevel) * 10)

    def do(line, config=False):
        cfg = 'CFG' if config else 'CLI'
        print("{}: '{}' ==> ".format(cfg, line), end='')
        if config:
            if w.config(line):
                print("OK")
                return

        if not config:
            if w.execCLI(line):
                print("OK\n{}".format(w.output))
                return

        print("ERR:\n{}".format(w.output))

    def config(line):
        do(line, True)

    def execCLI(line):
        do(line)

    # Create the WSMA utility
    with wsma.HTTP(args.host, args.username, args.password,
                   port=args.port, tls=not args.notls) as w:
        # do we have a working connection?
        if w is None:
            logging.critical('something went wrong, aborting...')
            exit()

        # Exec commands that use parsing to structured data on
        # router or switch. Not recommended
        print("\n### Available format specs:\n")
        execCLI('show format built-in')

        print("\n### Use built-in format specification:\n")
        cmds = ['show ip interface brief', 'show inventory']
        for cmd in cmds:
            w.execCLI(cmd, format_spec='builtin')
            if w.success:
                import json
                print(json.dumps(w.odmFormatResult, indent=2))

        '''
        # beware: execCLI does not like multi-line commands
        w.execCLI("""show inventory\nshow ip interface brief""",
                  format_spec='builtin')
        if w.success:
            import json
            print(json.dumps(w.odmFormatResult, indent=2))
        else:
            print(w.output)

        '''

        # behaves weird
        # filter only affects output from second command
        # but adding filter to first command does not working
        # as expected
        print("\n### mult-line exec command\n")
        execCLI("""show int gi1
show version | inc Cisco""")

        print("\n### Mixed exec/config mult-line input\n")
        config("""interface Loopback99
show interface Loop99
no interface Loop99""")

        print("\n### Single line commands\n")
        execCLI("show int lo99")
        config("no int Lo99")
        execCLI("show ip int br")

        print("\n### Look at IP routes and the IP routes summary\n")
        execCLI("show running-config | sec router ospf")
        execCLI("show ip route")
        execCLI("show ip route summary")

        print("\n### Negative tests, one for exec, one for config\n")
        execCLI("show ip intbr")
        config("nonsense command")

if __name__ == "__main__":
    main(sys.argv)

