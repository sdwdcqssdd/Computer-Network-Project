import socket
import argparse
import signal
import threading
import time

from serving_thread import ServerThread


class ListeningThread(threading.Thread):
    listen_port = None

    def __init__(self, listen_socket):
        threading.Thread.__init__(self)
        self.daemon = True
        self.listen_port = listen_socket

    def run(self):
        self.listen_port.listen(10)
        while True:
            client_socket, client_addr = self.listen_port.accept()
            print("connected from: ", client_addr)
            http_server = ServerThread(client_socket, client_addr)
            http_server.start()


def ForceExit(arg1, arg2):
    print("Ctrl+C, forced exit")
    exit(0)


if __name__ == '__main__':
    # use Ctrl+C to kill the sever
    signal.signal(signal.SIGINT, ForceExit)

    # add terminal arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", type=str, help="input IP address to start server")
    parser.add_argument("-p", type=int, help="input port number to start server on")

    # parse arguments
    args = parser.parse_args()
    server_IP = args.i
    server_port = args.p

    # create listening socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_IP, server_port))

    # create listening thread
    listen_thread = ListeningThread(server_socket)
    listen_thread.start()

    # do not stop the main thread
    while True:
        time.sleep(1)
