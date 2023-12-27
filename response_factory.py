# generate HTTP 400 Bad Request response
class ResponseFactory:
    @classmethod
    def http_400_bad_request(self):
        content = b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n'
        content += b'<html>\n'
        content += b'<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n'
        content += b'<title>Error response</title>\n'
        content += b'</head>\n'
        content += b'<body>\n'
        content += b'<h1>Error response</h1>\n'
        content += b'<p>Error code: 400</p>\n'
        content += b'<p>Message: Bad request.</p>\n'
        content += b'<p>Error code explanation: Request format is not invalid.</p>\n'
        content += b'</body>\n'
        content += b'</html>\n'

        head = b"HTTP/1.1 400 Bad request\r\n"
        head += b"Server: HTTPServer\r\n"
        head += b"Content-type: text/html; charset=utf-8\r\n"
        head += b"Content-Length: " + str(len(content)).encode('utf-8') + b'\r\n'
        head += b"\r\n"

        response = head + content
        return response

    # generate HTTP 403 Forbidden response
    @classmethod
    def http_403_forbidden(self):
        content = b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n'
        content += b'<html>\n'
        content += b'<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n'
        content += b'<title>Error response</title>\n'
        content += b'</head>\n'
        content += b'<body>\n'
        content += b'<h1>Error response</h1>\n'
        content += b'<p>Error code: 403</p>\n'
        content += b'<p>Message: Forbidden.</p>\n'
        content += b'<p>Error code explanation: Access to this resource on the server is denied.</p>\n'
        content += b'</body>\n'
        content += b'</html>\n'

        head = b"HTTP/1.1 403 Forbidden\r\n"
        head += b"Server: HTTPServer\r\n"
        head += b"Content-type: text/html; charset=utf-8\r\n"
        head += b"Content-Length: " + str(len(content)).encode('utf-8') + b'\r\n'
        head += b"\r\n"

        response = head + content
        return response

    # generate HTTP 404 File not found response
    @classmethod
    def http_404_not_found(self):
        content = b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n'
        content += b'<html>\n'
        content += b'<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n'
        content += b'<title>Error response</title>\n'
        content += b'</head>\n'
        content += b'<body>\n'
        content += b'<h1>Error response</h1>\n'
        content += b'<p>Error code: 404</p>\n'
        content += b'<p>Message: File not found.</p>\n'
        content += b'<p>Error code explanation: HTTPStatus.NOT_FOUND - Nothing matches the given URL.</p>\n'
        content += b'</body>\n'
        content += b'</html>\n'

        head = b"HTTP/1.1 404 File not found\r\n"
        head += b"Server: HTTPServer\r\n"
        head += b"Content-type: text/html; charset=utf-8\r\n"
        head += b"Content-Length: " + str(len(content)).encode('utf-8') + b'\r\n'
        head += b"\r\n"

        response = head + content
        return response

    # generate HTTP 405 Method Not Allowed response
    @classmethod
    def http_405_method_not_allowed(self):
        content = b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">\n'
        content += b'<html>\n'
        content += b'<meta http-equiv="Content-Type" content="text/html; charset=utf-8">\n'
        content += b'<title>Error response</title>\n'
        content += b'</head>\n'
        content += b'<body>\n'
        content += b'<h1>Error response</h1>\n'
        content += b'<p>Error code: 405</p>\n'
        content += b'<p>Message: Method Not Allowed.</p>\n'
        content += b'<p>Error code explanation: The requested method is not allowed for the specified resource.</p>\n'
        content += b'</body>\n'
        content += b'</html>\n'

        head = b"HTTP/1.1 405 Method Not Allowed\r\n"
        head += b"Server: HTTPServer\r\n"
        head += b"Content-type: text/html; charset=utf-8\r\n"
        head += b"Content-Length: " + str(len(content)).encode('utf-8') + b'\r\n'
        head += b"\r\n"

        response = head + content
        return response

    @classmethod
    def http_401_unauthorized(self):
        head = b"HTTP/1.1 401 Unauthorized\r\n"
        head += b"WWW-Authenticated: Basic realm='Authorization Required'\r\n"
        head += b"\r\n"
        return head

    @classmethod
    def http_200_ok(self):
        return b"HTTP/1.1 200 OK\r\nServer: HTTPServer\r\n"
