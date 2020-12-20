#!/usr/bin/python
from __future__ import print_function
import os
import sys
import requests
from sys import stderr
from urlparse import urlparse
from threading import Thread
from time import sleep
import socket
from select import poll, POLLIN, POLLPRI, POLLOUT, POLLHUP, POLLERR
from libproxy import ProxyFactory
from Queue import Queue, Empty


pf = ProxyFactory()


def unset_envvars():
    """Remove proxy envvars if set. We leave NO_PROXY alone."""
    for key in "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY":
        if key in os.environ:
            del os.environ[key]


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    server.bind(("127.0.0.1", 1234))
    server.listen(1)

    bridge = {}
    message_queues = {}
    sock_fd_to_sock = {
        server.fileno(): server
    }

    closing = {}

    READ_ONLY = POLLIN | POLLPRI | POLLHUP | POLLERR
    WRITE_ONLY = POLLOUT | POLLHUP | POLLERR
    READ_WRITE = READ_ONLY | POLLOUT
    p = poll()
    p.register(server, READ_ONLY)

    print("Ready to accept connections")
    while True:
        print("Open connections: {}".format(len(sock_fd_to_sock)))
        for sock_fd, event in p.poll():
            sock = sock_fd_to_sock[sock_fd]

            if event & (POLLIN | POLLPRI):
                if sock is server:
                    conn, addr = server.accept()
                    sock_fd_to_sock[conn.fileno()] = conn
                    p.register(conn, READ_ONLY)

                    message_queues[conn] = Queue()
                else:
                    data = sock.recv(1024)
                    if data:
                        if sock in bridge:  # Bridge
                            dst = bridge[sock]
                            message_queues[dst].put(data)
                            p.modify(dst, READ_WRITE)
                        else:  # Proxy
                            assert "\n" in data
                            cmd, url, http = data[:data.find("\n")].split()
                            if cmd != "GET":
                                print(cmd)
                                sys.exit(1)

                            print("Visit URL ", url)

                            message_queues[sock].put(data)
                            for proxy in pf.getProxies(url):
                                if proxy == "direct://":
                                    o = urlparse(url)
                                    new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                    new_sock.connect((o.hostname, o.port or 80))
                                elif proxy.startswith("http://"):
                                    print("+ HTTP Proxy {}".format(proxy), file=stderr)
                                    o = urlparse(proxy)
                                    new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                    new_sock.connect((o.hostname, o.port))
                            p.register(new_sock, READ_WRITE)
                            sock_fd_to_sock[new_sock.fileno()] = new_sock
                            message_queues[new_sock] = message_queues[sock]
                            message_queues[sock] = Queue()
                            bridge[sock] = new_sock
                            bridge[new_sock] = sock
                    else:  # no data
                        other = bridge.get(sock, None)

                        p.unregister(sock)
                        del sock_fd_to_sock[sock.fileno()]
                        del message_queues[sock]
                        del bridge[sock]
                        sock.close()
                        if other is not None:
                            p.modify(other, WRITE_ONLY)
                            closing[other] = True
                        continue

            elif event & POLLOUT:
                try:
                    next_msg = message_queues[sock].get_nowait()
                    sent = sock.send(next_msg)
                    assert sent > 0

                except Empty:
                    if sock in closing:
                        p.unregister(sock)
                        del sock_fd_to_sock[sock.fileno()]
                        del message_queues[sock]
                        del bridge[sock]
                        del closing[sock]
                        sock.close()
                    else:
                        p.modify(sock, READ_ONLY)
            else:
                print("Unknown event: {}".format(event))


def main():
    unset_envvars()
    start_server()


if __name__ == "__main__":
    main()
