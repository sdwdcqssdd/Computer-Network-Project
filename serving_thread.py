import base64
import mimetypes
import threading
import os
import json
import uuid
import shutil
import time
import socket
from response_factory import ResponseFactory

directory_path = "."
subdirectories = [name for name in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, name))]
folder = "data"

# the path of authentication information
auth_path = "./userInfo.json"
session_path = "./sessionInfo.json"


# used to check user info
def authenticate_by_auth(auth_info):
    info = base64.b64decode(auth_info).decode().split(":")
    if len(info) != 2:  # format error
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
                        print("Auth info:", username, password)
                        return True, username
                    else:
                        # password wrong
                        return False, None
                except (json.decoder.JSONDecodeError, KeyError):
                    # no such user
                    return False, None
    else:
        # file not found (server's mistake)
        return False, None


def set_cookie(username):
    print(session_path)
    if os.path.exists(session_path):
        lock = ServerThread.file_locks[session_path]
        print("cookie path right")
        with lock:
            print("get cookie lock")
            with open(session_path, 'r+') as session_file:
                print("open success")
                try:
                    data = json.load(session_file)
                    print("load Cookie")
                    session_id = str(uuid.uuid1().hex)
                    data[session_id] = {
                        "username": username,
                        "time_expire": time.time() + 60
                    }
                    session_file.seek(0)
                    session_file.write(json.dumps(data))
                    print("write Cookie")
                    return session_id
                except (json.decoder.JSONDecodeError, KeyError):
                    return None


def authenticate_by_cookie(cookie_info):
    if os.path.exists(session_path):
        lock = ServerThread.file_locks[session_path]
        with lock:
            with open(session_path, 'r') as session_file:
                try:
                    data = json.load(session_file)
                    if cookie_info in data and data[cookie_info]["time_expire"] >= time.time():
                        return True
                    return False
                except (json.decoder.JSONDecodeError, KeyError):
                    return False

def judgePara(parameters):
    para = parameters.split("&")
    for p in para:
        arg, val = p.split('=')
        if arg == 'SUSTech-HTTP':
            if val == '0':
                pass
            elif val == '1':
                pass
            else:
                return False
        elif arg == 'chunked':
            if val == '0':
                pass
            elif val == '1':
                pass
            else:
                return False
        else:
            return False    
    return True        

# main server thread, handle requests of a user
class ServerThread(threading.Thread):
    # every file needs a lock, in case of read-write conflict
    # key: root_path; value: file_lock
    # need to add lock when upload a new file, and remove lock when delete a file
    auth_lock = threading.Lock()
    session_lock = threading.Lock()
    file_locks = {auth_path: auth_lock, session_path: session_lock}

    def __init__(self, client_socket, client_addr):
        threading.Thread.__init__(self)
        self.daemon = True
        self.client_socket = client_socket
        self.client_address = client_addr
        self.username = None

    def run(self):
        while True:
            try:
                request = self.client_socket.recv(4096)
                self.client_socket.settimeout(0.05)
                while True:
                    try:
                        data = self.client_socket.recv(4096)
                        request += data
                    except socket.timeout:
                        self.client_socket.settimeout(None)
                        break 
                print("get a request of thread", self.name)
                print("request content:", repr(request))
                lines = request.split(b"\r\n")
                cookie_verification = False

                authentication_auth = False  # need to check every request
                authentication_cookie = False
                session_id = None
                close = False
                url = None
                method = None
                boundary = None
                # try:
                #     body = request.split("\r\n\r\n")[1]
                # except IndexError:
                #     self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                #     return

                # if lines[0].startswith('GET'):
                #     pass
                # elif lines[0].startswith('POST'):
                #     pass
                # elif lines[0].startswith('HEAD'):
                #     pass
                # else:
                #     self.client_socket.sendall(ResponseFactory.http_405_method_not_allowed())
                #     continue

                for line in lines:
                    if line.startswith(b"GET"):
                        print("GET method")
                        method = "get"
                        contents = line.split(b" ")
                        url = contents[1].decode()
                        print(url)
                    elif line.startswith(b"Connection:"):
                        print("Check close request")
                        content = line.split(b":", 1)[1].decode().strip()
                        if content.lower() == "close":
                            close = True
                    elif line.startswith(b"Authorization:"):
                        print("Have Auth Info")
                        content = line.split(b" ")
                        if len(content) != 3:
                            # format error, authentication should be False
                            continue
                        auth_type = content[1].decode().strip()
                        auth_content = content[2].decode().strip()
                        if auth_type != "Basic":
                            # only accept Basic, authentication should be False
                            continue
                        authentication_auth, self.username = authenticate_by_auth(auth_content)
                    elif line.startswith(b"Cookie:"):
                        print("Have Cookie Info")
                        session_id = line.split(b"session-id=")[1].decode()
                        print(session_id)
                        authentication_cookie = authenticate_by_cookie(session_id)
                    elif line.startswith(b"POST"):
                        print("POST Method")
                        method = "post"
                        contents = line.split(b" ")
                        url = contents[1].decode()
                        print(url)
                    elif line.startswith(b"HEAD"):
                        print("HEAD Method")
                        method = "head"
                        contents = line.split(b" ")
                        url = contents[1].decode()
                        print(url)
                    elif line.startswith(b"Content-Type:"):
                        bound = line.split(b"boundary=")
                        if len(bound) == 2:
                            boundary = bound[1].decode()
                if not authentication_cookie:
                    if not authentication_auth:
                        self.client_socket.sendall(ResponseFactory.http_401_unauthorized())
                        print("Authentication Failed")
                        continue
                    else:
                        # first time session/cookie
                        session_id = set_cookie(self.username)
                        print(f"first time session/cookie, session_id is {session_id}")
                    # go to verify if the client want to close connection after this request

                if url is not None:
                    self.URL_handler(method, url, boundary, session_id, request)

                else:
                    response = ResponseFactory.http_200_ok()
                    response += b"Content-Type: application/octet-stream\r\n"
                    response += b"Content-Length: 0\r\n"
                    if session_id:
                        response += f'Set-Cookie: session-id={session_id}\r\n'.encode()
                    response += b"\r\n"
                    self.client_socket.sendall(response)
            except ConnectionAbortedError:  # in case the user close the connection suddenly without informing
                self.client_socket.close()
                break
            if close:
                self.client_socket.close()
                print("Connection Closed")
                break

    def URL_handler(self, method, url, boundary, session_id, request):
        query = url.split("?")
        print("param info:", query)
        param_num = len(query) - 1
        Match = False
        forbidden = False
        if param_num == 0:  # no parameter
            path = "./data" + query[0]
            if method == 'head':
                Match = True
            elif method == 'get':
                Match = True    
        elif param_num == 1:
            path = "./data" + query[0]
            if query[1] == "":
                self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                return 
            elif judgePara(query[1]):
                if method == 'head':
                    Match = True
                elif method == 'get':
                    Match = True 
            else:         
                try:
                    func = query[0][-6:]  # function name, just before '?'
                    print("URL function:", func)
                    path = ""
                    if query[1].startswith("path="):
                        try:
                            path = query[1][5:]  # parse the directory
                            if path[0] == '/':
                                path = "./data" + path
                            else:
                                path = "./data/" + path
                            print("Full path:", path)
                            authority = path.split("/")[2]
                            print("whose folder:", authority)
                            if authority != self.username:  # have no authority
                                forbidden = True
                        except IndexError:
                            # path is null
                            self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                            return
                        if func == "upload":
                            if forbidden:
                                self.client_socket.sendall(ResponseFactory.http_403_forbidden())
                                return
                            if path[-1] != '/':
                                path += "/"
                            print("upload path:", path)
                            if not os.path.isdir(path):
                                # can only upload to a folder
                                print("upload path not folder")
                                self.client_socket.sendall(ResponseFactory.http_404_not_found())
                                return
                            if method != "post":
                                self.client_socket.sendall(ResponseFactory.http_405_method_not_allowed())
                                return
                            self.upload(path, request, boundary, session_id)
                            return
                                
                        elif func == "delete":
                            if forbidden:
                                self.client_socket.sendall(ResponseFactory.http_403_forbidden())
                                return
                            if not os.path.exists(path):
                                self.client_socket.sendall(ResponseFactory.http_404_not_found())
                                return
                            if method != "post":
                                self.client_socket.sendall(ResponseFactory.http_405_method_not_allowed())
                                return
                            self.delete(path, session_id)
                            return

                        else:
                            # unsupported function, URL cannot be resolved
                            self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                            return
                    else:
                        self.client_socket.sendall(ResponseFactory.http_400_bad_request()) 
                        
                except IndexError:
                    # format error or function unsupported
                    self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                    return
        else:
            self.client_socket.sendall(ResponseFactory.http_400_bad_request())
            return
        
        # if forbidden:
        #     self.client_socket.sendall(ResponseFactory.http_403_forbidden())
        #     return

        if os.path.exists(path):
            pass
        else:
            self.client_socket.sendall(ResponseFactory.http_404_not_found())
            return
        
        if Match == False:
            self.client_socket.sendall(ResponseFactory.http_405_method_not_allowed())
            return
        
        if method == 'get':
            self.view(url, session_id)
        elif method == 'head':
            print("perform HEAD")
            self.Head(url, session_id)
        else:
            self.client_socket.sendall(ResponseFactory.http_400_bad_request())
            return
        # else:
        #     if func == "upload":
        #         self.upload(path, request, boundary, session_id)
        #     else:
        #         self.delete(path, session_id)




    def Head(self, url, session_id):
        parts = url.split("?")
        parameter = None
        if len(parts) == 1:
            addr = parts[0]
            addr = "./" + folder + addr
            response = ResponseFactory.http_200_ok()
            response += b"Content-Type: text/html\r\n"
            response += b"Content-Length: 0\r\n"
            if session_id:
                response += f'Set-Cookie: session-id={session_id}\r\n'.encode()
            response += b"\r\n"
            self.client_socket.sendall(response)
            return
        else:
            addr = parts[0]
            addr = "./" + folder + addr
            parameter = parts[1]
            print("HEAD: URL valid")
            response = ResponseFactory.http_200_ok()
            response += b"Content-Type: text/html\r\n"
            response += b"Content-Length: 0\r\n"
            if session_id:
                response += f'Set-Cookie: session-id={session_id}\r\n'.encode()
            response += b"\r\n"
            self.client_socket.sendall(response)
            return


    def view(self, url, session_id):
        parts = url.split("?")
        parameter = None
        SUSTech_HTTP = 0 
        chunked = 0
        if len(parts) == 1:
            addr = parts[0]
            addr = "./" + folder + addr
        else:
            addr = parts[0]
            addr = "./" + folder + addr
            parameter = parts[1]
        
        if parameter:
            para = parameter.split("&")
            for p in para:
                arg, val = p.split('=')
                if arg == 'SUSTech-HTTP':
                    if val == '0':
                        SUSTech_HTTP = 0
                    elif val == '1':
                        SUSTech_HTTP = 1
                elif arg == 'chunked':
                    if val == '0':
                        chunked = 0
                    elif val == '1':
                        chunked = 1

        if os.path.isfile(addr):
            self.download(addr,chunked, session_id)
            return
        

        else:
            if SUSTech_HTTP == 0:
                contents = os.listdir(addr)
                head = (ResponseFactory.http_200_ok()
                        + b"Content-type: text/html; charset=utf-8\r\n"
                        )
                if session_id:
                    head += f'Set-Cookie: session-id={session_id}\r\n'.encode()
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
                print(response)
                self.client_socket.sendall(response)
                return

            else:
                contents = os.listdir(addr)
                content = json.dumps(contents)
                head = (ResponseFactory.http_200_ok()
                        + b"Content-type: application/json\r\n"
                        + b"Content-Length: " + str(len(content)).encode('utf-8') + b"\r\n"
                        )
                if session_id:
                    head += f'Set-Cookie: session-id={session_id}\r\n'.encode()
                head += b'\r\n'
                content = content.encode("utf-8")
                response = head + content
                self.client_socket.sendall(response)
                return
            
        

    def download(self,addr,chuncked, session_id):
        mime_type, encoding = mimetypes.guess_type(addr)
        head = (ResponseFactory.http_200_ok() + b"Content-type: ")
        if mime_type:
            head += mime_type.encode('utf-8')
        else:
            head += b'application/octet-stream'
        if encoding:
            head += b"; charset=" + encoding.encode('utf-8')
        head += b'\r\n'
        if session_id:
            head += f'Set-Cookie: session-id={session_id}\r\n'.encode()
        with open(addr, 'rb') as f:
            content = f.read()


        if chuncked == 0:
            try:
                with open(addr, 'rb') as f:
                    content = f.read()
                length = len(content)
                head = head + b'Content-Length: ' + str(length).encode('utf-8') + b'\r\n\r\n'
                response = head + content
                self.client_socket.sendall(response)
                return
            except MemoryError:
                self.client_socket.sendall(ResponseFactory.http_503_service_temporarily_unavailable())
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

    # def handle_post(self, url, request, boundary):
    #     upload = False
    #     delete = False
    #     analyze = url.split("?")
    #     print("upload or delete path:", analyze)
    #     if len(analyze) != 2:  # no parameter
    #         self.client_socket.sendall(ResponseFactory.http_400_method_not_allowed())
    #         return
    #     else:
    #         try:
    #             func = analyze[0][-6:]
    #             print("upload or delete:", func)
    #             path = ""
    #             if analyze[1].startswith("path="):
    #                 try:
    #                     path = analyze[1][5:]
    #                     if path[0] == '/':
    #                         path = "./data" + path
    #                     else:
    #                         path = "./data/" + path
    #                     print("Full path:", path)
    #                     authority = path.split("/")[2]
    #                     print("whose folder:", authority)
    #                     if authority != self.username:  # have no authority
    #                         self.client_socket.sendall(
    #                             ResponseFactory.http_403_forbidden())  # Not the current user's folder
    #                         return
    #                 except IndexError:
    #                     # path is null
    #                     self.client_socket.sendall(ResponseFactory.http_400_bad_request())
    #                     return
    #             else:
    #                 self.client_socket.sendall(ResponseFactory.http_400_bad_request())  # Do not have parameter "path"
    #             if func == "upload":
    #                 self.upload(path, request, boundary)
    #             elif func == "delete":
    #                 self.delete(path)
    #             else:
    #                 # unsupported function
    #                 self.client_socket.sendall(ResponseFactory.http_405_method_not_allowed())
    #                 return
    #         except IndexError:
    #             # format error or function unsupported
    #             self.client_socket.sendall(ResponseFactory.http_400_bad_request())
    #             return

    def upload(self, path, request, boundary, session_id):
        if boundary is None:
            # format error
            self.client_socket.sendall(ResponseFactory.http_400_bad_request())
            return
        bound = "--" + boundary
        if path[-1] != '/':
            path += "/"
        print("upload path:", path)
        if not os.path.isdir(path):
            # can only upload to a folder
            print("upload path not folder")
            self.client_socket.sendall(ResponseFactory.http_404_not_found())
            return
        else:
            lines = request.split(b"\r\n")
            for line in lines:  
                if line.startswith(b"Content-Disposition:"):
                    try:
                        name = line.split(b"filename=")[1].decode()
                        file_name = name.strip()[1:-1]
                        print("upload filename:", file_name)
                    except IndexError:
                        # cannot find filename
                        print("no filename")
                        self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                    path += file_name
                    break
            if path[-1] == '/':
                # cannot upload a folder
                self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                return
            file_body = request.split(bound.encode())
            if len(file_body) != 3:
                # format error
                print("bound error", file_body, bound)
                self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                return
            file_content = file_body[1].split(b"\r\n\r\n")
            # print("upload file content:", file_content)
            try:
                data = file_content[1].strip(b"")
                with open(path, "wb") as file_writer:
                    file_writer.write(data)
                response = ResponseFactory.http_200_ok()
                response += b"Content-Type: application/octet-stream\r\n"
                response += b"Content-Length: 0\r\n"
                if session_id:
                    response += f'Set-Cookie: session-id={session_id}\r\n'.encode()
                response += b"\r\n"
                print("upload response:", repr(response))
                self.client_socket.sendall(response)
                print("upload success")
            except IndexError:
                # no data
                self.client_socket.sendall(ResponseFactory.http_400_bad_request())
                return

        # wait for the answer of the issue
        # response = ResponseFactory.http_200_ok() + b"\r\n"
        # self.client_socket.sendall(response)
        # return

    def delete(self, path, session_id):
        # if not os.path.exists(path):
        #     self.client_socket.sendall(ResponseFactory.http_404_not_found())
        #     return
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path)
        response = ResponseFactory.http_200_ok()
        response += b"Content-Type: application/octet-stream\r\n"
        response += b"Content-Length: 0\r\n"
        if session_id:
            response += f'Set-Cookie: session-id={session_id}\r\n'.encode()
        response += b"\r\n"
        print("delete response:", repr(response))
        self.client_socket.sendall(response)
        print("delete success")
        return
