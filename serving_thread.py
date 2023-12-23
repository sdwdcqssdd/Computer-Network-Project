import base64
import mimetypes
import socket
import threading
import sys
import os
import json

directory_path = "."
subdirectories = [name for name in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, name))]
folder = "data"


class ServerThread(threading.Thread):
    lock = threading.Lock()

    def __init__(self, client_socket, client_addr):
        threading.Thread.__init__(self)
        self.daemon = True
        self.client_socket = client_socket
        self.client_address = client_addr

    def run(self):
        while True:
            print("get request")
            request = self.client_socket.recv(1024).decode()
            lines = request.split("\r\n")
            authentication = False
            close = False
            url = None

            for line in lines:
                if line.startswith("GET"):
                    contents = line.split(" ")
                    url = contents[1]
                elif line.startswith("Connection:"):
                    content = line.split(":", 1)[1].strip()
                    if content.lower() == "close":
                        close = True
                elif line.startswith("Authorization:"):
                    content = line.split(" ")
                    if len(content) != 3:
                        # return 401
                        continue
                    auth_type = content[1].strip()
                    auth_content = content[2].strip()
                    if auth_type != "Basic":
                        continue
                    authentication = self.authenticate(auth_content)

            if not authentication:
                head = (
                        b"HTTP/1.1 401 Unauthorized\r\n"
                        + b"WWW-Authenticated: Basic realm='Authorization Required'\r\n"
                        + b"\r\n"
                )
                self.client_socket.sendall(head)
                print("Not Authenticated")
            elif url is not None:
                self.view(url)

            if close:
                self.client_socket.close()
                print("closed")
                break

    def authenticate(self, author):
        info = base64.b64decode(author)
        info = info.split(":")
        if len(info) != 2:
            return False
        username = info[0].strip()
        password = info[1].strip()

    def view(self, url):
        parts = url.split("?")
        parameter = None
        if len(parts) == 1:
            addr = parts[0]
            addr = "./" + folder + addr
        else:
            addr = parts[0]
            addr = folder + addr
            parameter = parts[1]
        if os.path.exists(addr):
            if os.path.isfile(addr):
                self.download(addr, parameter)
                return
            else:
                if (parameter == "SUSTech-HTTP=0") or (parameter is None):
                    contents = os.listdir(addr)
                    head = (b"HTTP/1.1 200 OK\r\n"
                            + b"Sever: HTTPServer\r\n"
                            + b"Content-type: text/html; charset=utf-8\r\n"
                            )
                    content = (
                            b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n'
                            + b'<html>\n'
                            + b'<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n'
                            + b'<title>Directory listing for ' + addr.encode('utf-8') + b'</title>\n'
                            + b'</head>\n'
                            + b'<body>\n'
                            + b'<h1>Directory listing for ' + addr.encode('utf-8') + b'</h1>\n'
                            + b'<hr>\n'
                            + b'<ul>\n')

                    for item in contents:
                        item_path = os.path.join(addr, item)
                        if os.path.isdir(item_path):
                            item = item + '/'
                        content = content + b'<li><a href="' + item.encode('utf-8') + b'">' + item.encode(
                            'utf-8') + b'</a></li>\n'
                    content = content + b'</ul>\n<hr>\n</body>\n</html>\n'
                    length = len(content)
                    head = head + b'Content-Length: ' + str(length).encode('utf-8') + b'\r\n\r\n'
                    response = head + content
                    self.client_socket.sendall(response)
                    return

                elif parameter == "SUSTech-HTTP=1":
                    contents = os.listdir(addr)
                    content = json.dumps(contents)
                    head = (b"HTTP/1.1 200 OK\r\n"
                            + b"Sever: HTTPServer\r\n"
                            + b"Content-type: application/json\r\n"
                            + b"Content-Length: " + str(len(content)).encode('utf-8') + b"\r\n\r\n"
                            )
                    content = content.encode("utf-8")
                    response = head + content
                    self.client_socket.sendall(response)
                    return
                else:
                    head = (b"HTTP/1.1 400 Bad request\r\n"
                            + b"Sever: HTTPServer\r\n"
                            + b"Content-type: text/html; charset=utf-8\r\n"
                            )
                    content = (
                            b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n'
                            + b'<html>\n'
                            + b'<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n'
                            + b'<title>Error response</title>\n'
                            + b'</head>\n'
                            + b'<body>\n'
                            + b'<h1>Error response</h1>\n'
                            + b'<p>Error code: 400</p>\n'
                            + b'<p>Message: Bad request.</p>\n'
                            + b'<p>Error code explanation: Request format is not invalid.</p>\n'
                            + b'</body>\n'
                            + b'</html>\n'
                    )
                    length = len(content)
                    head = head + b'Content-Length: ' + str(length).encode('utf-8') + b'\r\n\r\n'
                    response = head + content
                    self.client_socket.sendall(response)
                    return
        else:
            head = (b"HTTP/1.1 404 File not found\r\n"
                    + b"Sever: HTTPServer\r\n"
                    + b"Content-type: text/html; charset=utf-8\r\n"
                    )
            content = (b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n'
                       + b'<html>\n'
                       + b'<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n'
                       + b'<title>Error response</title>\n'
                       + b'</head>\n'
                       + b'<body>\n'
                       + b'<h1>Error response</h1>\n'
                       + b'<p>Error code: 404</p>\n'
                       + b'<p>Message: File not found.</p>\n'
                       + b'<p>Error code explanation: HTTPStatus.NOT_FOUND - Nothing matches the given URL.</p>\n'
                       + b'</body>\n'
                       + b'</html>\n'
                       )
            length = len(content)
            head = head + b'Content-Length: ' + str(length).encode('utf-8') + b'\r\n\r\n'
            response = head + content
            self.client_socket.sendall(response)
            return

    def download(self, addr, parameter):
        mime_type, encoding = mimetypes.guess_type(addr)
        head = (b"HTTP/1.1 200 OK\r\n"
                + b"Sever: HTTPServer\r\n"
                + b"Content-type: " + mime_type.encode('utf-8')
                )
        if encoding:
            head += b"; charset=" + encoding.encode('utf-8')
        head += b"\r\n"
        with open(addr, 'rb') as f:
            content = f.read()

        if (parameter is None) or parameter.startswith("SUSTech-HTTP=") or parameter == 'chunked=0':
            length = len(content)
            head = head + b'Content-Length: ' + str(length).encode('utf-8') + b'\r\n\r\n'
            response = head + content
            self.client_socket.sendall(response)
            return


        elif parameter == 'chunked=1':
            head += b'Transfer-Encoding: chunked\r\n\r\n'
            self.client_socket.sendall(head)

            chunk_size = 1024
            with open(addr, 'rb') as f:
                while True:
                    chunk_data = f.read(chunk_size)
                    if not chunk_data:
                        break
                    chunk_length = hex(len(chunk_data))[2:].encode('utf-8') + b'\r\n'
                    chunk_data += b'\r\n'
                    chunk = chunk_length + chunk_data
                    self.client_socket.sendall(chunk)
            self.client_socket.sendall(b'0\r\n\r\n')
            return

        else:
            head = (b"HTTP/1.1 400 Bad request\r\n"
                    + b"Sever: HTTPServer\r\n"
                    + b"Content-type: text/html; charset=utf-8\r\n"
                    )
            content = (b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n'
                       + b'<html>\n'
                       + b'<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n'
                       + b'<title>Error response</title>\n'
                       + b'</head>\n'
                       + b'<body>\n'
                       + b'<h1>Error response</h1>\n'
                       + b'<p>Error code: 400</p>\n'
                       + b'<p>Message: Bad request.</p>\n'
                       + b'<p>Error code explanation: Request format is not invalid.</p>\n'
                       + b'</body>\n'
                       + b'</html>\n'
                       )
            length = len(content)
            head = head + b'Content-Length: ' + str(length).encode('utf-8') + b'\r\n\r\n'
            response = head + content
            self.client_socket.sendall(response)
            return
