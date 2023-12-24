import socket
import threading
import time
import argparse
import signal

from serving_thread import ServerThread


class ListeningThread(threading.Thread):
    listen_sock = None

    def __init__(self, listen_socket):
        threading.Thread.__init__(self)
        self.daemon = True
        ListeningThread.listen_sock = listen_socket

    def run(self):
        while True:
            client_socket, client_addr = ListeningThread.listen_sock.accept()
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
    server_socket.listen(10)

    # create listening thread
    listen_thread = ListeningThread(server_socket)
    listen_thread.start()

    # do not stop the main thread
    while True:
        time.sleep(1)


# lab4 lab slides

# def echo():
#     sock = socket.socket(socket.AF_INET,
#                          socket.SOCK_STREAM)
#     sock.bind(('127.0.0.1', 8080))
#     sock.listen(10)
#     while True:
#         conn, address = sock.accept()
#         Echo(conn, address).start()
#
#
# class Echo(threading.Thread):
#     def __init__(self, conn, address):
#         threading.Thread.__init__(self)
#         self.conn = conn
#         self.address = address
#
#     def run(self):
#         while True:
#             data = self.conn.recv(2048)
#             if data and data != b'exit':
#                 self.conn.send(data)
#                 print('{} sent: {}'.format(self.address, data))
#             else:
#                 self.conn.close()
#             return
#
#
# if __name__ == "__main__":
#     try:
#         echo()
#     except KeyboardInterrupt:
#         pass
