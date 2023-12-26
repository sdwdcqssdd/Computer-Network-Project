import socket
import argparse
import mimetypes
import os
import json

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 8080))
server_socket.listen(128)
directory_path = "."
subdirectories = [name for name in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, name))]
folder = subdirectories[0]

def ok():
    return b"HTTP/1.1 200 OK\r\nSever: HTTPServer\r\n"

def badRequest():
    return b"HTTP/1.1 400 Bad request\r\nSever: HTTPServer\r\n"

def fileNotFound():
    return b"HTTP/1.1 404 File not found\r\nSever: HTTPServer\r\n"

class HttpServer:

    def __init__(self):
        self.client_socket = None
        self.client_address = None
    
    def connect(self):
        self.client_socket,self.client_address = server_socket.accept()
        while True:
            request = self.client_socket.recv(1024).decode()
            lines = request.split("\r\n")
            close = False
            
            for line in lines:
                if line.startswith("GET"):
                    contents = line.split(" ")
                    url = contents[1]
                    self.view(url)
                elif line.startswith("Connection:"):
                    content = line.split(":",1)[1].strip()
                    if content.lower() == "close":
                        close = True

            if close:
                self.client_socket.close()
                break 

    def view(self,url):
        parts = url.split("?")
        parameter = None
        if len(parts) == 1:
            addr = parts[0]
            addr = "./"+folder+addr
        else:
            addr = parts[0]
            addr = folder+addr
            parameter = parts[1] 
        if os.path.exists(addr):
            if os.path.isfile(addr):
                self.download(addr,parameter)
                return
            else:
                if (parameter == "SUSTech-HTTP=0") or (parameter is None):
                    contents = os.listdir(addr)
                    head = (ok()
                        + b"Content-type: text/html; charset=utf-8\r\n"
                        )
                    content = (b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n'
                            + b'<html>\n'
                            + b'<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n'
                            + b'<title>Directory listing for ' + addr.encode('utf-8') + b'</title>\n'
                            + b'</head>\n'
                            + b'<body>\n'
                            + b'<h1>Directory listing for ' + addr.encode('utf-8') + b'</h1>\n'
                            + b'<hr>\n'
                            + b'<ul>\n')
                    
                    for item in contents:
                        item_path = os.path.join(addr,item)
                        if os.path.isdir(item_path):
                            item = item + '/'
                        content = content + b'<li><a href="' + item.encode('utf-8') + b'">' + item.encode('utf-8') + b'</a></li>\n'
                    content = content + b'</ul>\n<hr>\n</body>\n</html>\n'
                    length = len(content)
                    head = head + b'Content-Length: ' + str(length).encode('utf-8') + b'\r\n\r\n'
                    response = head + content
                    self.client_socket.sendall(response)
                    return
                
                elif parameter == "SUSTech-HTTP=1":
                    contents = os.listdir(addr)
                    content = json.dumps(contents)
                    head = (ok()
                          + b"Content-type: application/json\r\n"
                          + b"Content-Length: " + str(len(content)).encode('utf-8') + b"\r\n\r\n"
                    )
                    content = content.encode("utf-8")
                    response = head + content
                    self.client_socket.sendall(response)
                    return 
                else:
                    head = (badRequest()
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
        else:
            head = (fileNotFound()
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
        
    def download(self,addr,parameter):
        mime_type, encoding = mimetypes.guess_type(addr)
        head = (ok()
                + b"Content-type: " + mime_type.encode('utf-8')
                )
        if encoding:
            head += b"; charset=" + encoding.encode('utf-8')
        head += b"\r\n"
        with open(addr,'rb') as f:
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
            with open(addr,'rb') as f:
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
            head = (badRequest()
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
        
if __name__ == '__main__':
    server = HttpServer()
    server.connect()



