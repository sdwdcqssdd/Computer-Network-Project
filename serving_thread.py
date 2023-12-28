import base64
import mimetypes
import threading
import os
import json
import shutil
from response_factory import ResponseFactory

directory_path = "."
subdirectories = [name for name in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, name))]
folder = "data"

# the path of authentication information
auth_path = "./userInfo.json"


# used to check user info
def authenticate(auth_info):
    info = base64.b64decode(auth_info).decode()
    info = info.split(":")
    if len(info) != 2:
        return False, None
    username = info[0].strip()
    password = info[1].strip()
    if os.path.exists(auth_path):
        auth_lock = ServerThread.file_locks[auth_path]
        with auth_lock:
            with open(auth_path, 'r') as auth_handler:
                try:
                    data = json.load(auth_handler)
                    if data[username]["password"] == password:
                        print(username, password)
                        return True, username
                    else:
                        return False, None
                except (json.decoder.JSONDecodeError, KeyError):
                    return False, None
    else:
        return False, None


# main server thread, handle requests of a user
class ServerThread(threading.Thread):
    # every file needs a lock, in case of read-write conflict
    # key: root_path; value: file_lock
    # need to add lock when upload a new file, and remove lock when delete a file
    auth_lock = threading.Lock()
    file_locks = {auth_path: auth_lock}

    def __init__(self, client_socket, client_addr):
        threading.Thread.__init__(self)
        self.daemon = True
        self.client_socket = client_socket
        self.client_address = client_addr
        self.username = None

    def run(self):
        while True:
            try:
                request = self.client_socket.recv(1024).decode()
            except ConnectionAbortedError:  # in case the user close the connection suddenly without informing
                self.client_socket.close()
                break
            print("get request")
            print(repr(request))
            lines = request.split("\r\n")
            authentication = (self.username is None)  # username will be recorded after authentication
            close = False
            url = None
            get = False
            post = False
            Head = False
            try:
                body = request.split("\r\n\r\n")[1]
            except IndexError:
                self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                return

            if lines[0].startswith('GET'):
                pass
            elif lines[0].startswith('POST'):
                pass
            elif lines[0].startswith('HEAD'):
                pass
            else:
                self.client_socket.sendall(ResponseFactory.http_400_bad_request())
            
            for line in lines:
                if line.startswith("GET"):
                    print("GET method")
                    get = True
                    contents = line.split(" ")
                    url = contents[1]
                    print(url)
                elif line.startswith("Connection:"):
                    print("Check close request")
                    content = line.split(":", 1)[1].strip()
                    if content.lower() == "close":
                        close = True
                elif line.startswith("Authorization:"):
                    print("Have Auth Info")
                    content = line.split(" ")
                    if len(content) != 3:
                        # authentication should be False
                        continue
                    auth_type = content[1].strip()
                    auth_content = content[2].strip()
                    if auth_type != "Basic":
                        # authentication should be False
                        continue
                    authentication, self.username = authenticate(auth_content)
                elif line.startswith("POST"):
                    print("POST Method")
                    post = True
                    contents = line.split(" ")
                    url = contents[1]
                    print(url)
                elif line.startswith("HEAD"):
                    print("HEAD Method")
                    Head = True
                    contents = line.split(" ")
                    url = contents[1]
                    print(url)   

            if not authentication:
                self.client_socket.sendall(ResponseFactory.http_401_unauthorized())
                print("Not Authenticated")  # go to verify if the client want to close connection after this request
            elif url is not None:
                if get:
                    self.view(url)
                if post:
                    self.handle_post(url, body)
                if Head:
                    self.Head(url)
            else:
                self.client_socket.sendall(ResponseFactory.http_200_ok())

            if close:
                self.client_socket.close()
                print("closed")
                break

    def Head(self, url):
        parts = url.split("?")
        if len(parts) != 1:
            self.client_socket.sendall(ResponseFactory.http_400_bad_request())
            return
        else:
            addr = parts[0]
            addr = "./" + folder + addr    
            if os.path.exists(addr):
                self.client_socket.sendall(ResponseFactory.http_200_ok())
                return 
            else:
                self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                return


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
        if (parameter == "SUSTech-HTTP=0") or (parameter is None):
            pass
        elif parameter == "SUSTech-HTTP=1":
            pass
        else:
            self.client_socket.sendall(ResponseFactory.http_400_bad_request())
            return
        if os.path.exists(addr):
            if os.path.isfile(addr):
                self.download(addr, parameter)
                return
            else:
                if (parameter == "SUSTech-HTTP=0") or (parameter is None):
                    contents = os.listdir(addr)
                    head = (ResponseFactory.http_200_ok()
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
                    head = (ResponseFactory.http_200_ok()
                            + b"Content-type: application/json\r\n"
                            + b"Content-Length: " + str(len(content)).encode('utf-8') + b"\r\n\r\n"
                            )
                    content = content.encode("utf-8")
                    response = head + content
                    self.client_socket.sendall(response)
                    return
                else:
                    self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                    return
        else:
            self.client_socket.sendall(ResponseFactory.http_404_not_found())
            return

    def download(self, addr, parameter):
        mime_type, encoding = mimetypes.guess_type(addr)
        head = (ResponseFactory.http_200_ok() + b"Content-type: ")
        if mime_type:
            head += mime_type.encode('utf-8')
        else:
            head += b'application/octet-stream'    
        if encoding:
            head += b"; charset=" + encoding.encode('utf-8')
        head += b"\r\n"
        with open(addr, 'rb') as f:
            content = f.read()

        chuncked = False
        para = parameter.split("&")
        for p in para:
            arg, val = p.split('=')
            if arg == 'SUSTech-HTTP':
                continue
            elif arg == 'chunked':
                if val == '0':
                    chuncked = False
                elif val == '1':
                    chuncked = True
                else:
                    self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                    return
            else:
                self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                return            


        if chuncked:
            length = len(content)
            head = head + b'Content-Length: ' + str(length).encode('utf-8') + b'\r\n\r\n'
            response = head + content
            self.client_socket.sendall(response)
            return
        else:
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

    def handle_post(self, url, body):
        analyze = url.split("?")
        print(analyze)
        if len(analyze) != 2:
            self.client_socket.sendall(ResponseFactory.http_400_bad_request())
            return
        else:
            try:
                func = analyze[0][-6:]
                path = ""
                if analyze[1].startswith("path="):
                    try:
                        path = analyze[1][5:]
                        if path[0] == '/':
                            path = "./data" + path
                        else:
                            path = "./data/" + path
                        print(path)
                        authority = path.split("/")[2]
                        print(authority)
                        if authority != self.username:
                            self.client_socket.sendall(
                                ResponseFactory.http_403_forbidden())  # Not the current user's folder
                            return
                    except IndexError:
                        # path is null
                        self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                        return
                else:
                    self.client_socket.sendall(ResponseFactory.http_400_bad_request())  # Do not have parameter "path"
                if func == "upload":
                    self.upload(path, body)
                elif func == "delete":
                    self.delete(path)
                else:
                    self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                    return
            except IndexError:
                self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                return

    def upload(self, path, body):
        if path[-1] != '/':
            path += "/"
        print(path)
        if not os.path.isdir(path):
            self.client_socket.sendall(ResponseFactory.http_404_not_found())
            return
        else:
            pass
        # wait for the answer of the issue
        response = ResponseFactory.http_200_ok() + b"\r\n"
        self.client_socket.sendall(response)
        return

    def delete(self, path):
        if not os.path.exists(path):
            self.client_socket.sendall(ResponseFactory.http_404_not_found())
            return
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path)
        response = ResponseFactory.http_200_ok() + b"\r\n"
        self.client_socket.sendall(response)
        return
