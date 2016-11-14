#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" simple CLI tool, only show commands supported """

from __future__ import print_function
import wsma
from argparse import ArgumentParser
import logging
import readline
import sys

def main(argv):

    # enable logging
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

        # workaround Python3 vs. Python2 stuff
        try:
            input = raw_input
        except NameError:
            pass

        # simple command line interface
        done = False
        print('enter command, Ctl-D to quit')
        while not done:
            try:
                line = input("> ")
            except EOFError:
                print()
                done = True
            else:
                if len(line) > 0:
                    execCLI(line)
        # exit()


if __name__ == "__main__":
    main(sys.argv)

