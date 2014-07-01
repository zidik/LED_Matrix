__author__ = 'Mark'

from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import cgi
import logging
import threading


class MatrixWebserver(threading.Thread):
    def __init__(self, matrix_controller, address="localhost", port=80):
        super().__init__()
        self.matrix_controller = matrix_controller
        self.name = "Server thread"
        self.server = HTTPServer((address, port), MyHTTPRequestHandler)

    def run(self):
        logging.info("Server started.")
        self.server.serve_forever()

    def join(self, timeout=None):
        self.server.shutdown()
        logging.info("Server stopped.")
        super().join(timeout)


class MyHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            if self.path == "/":
                self.path = "test.html"

            send_reply = False
            mime_type = None
            if self.path.endswith(".html"):
                mime_type = 'text/html'
                send_reply = True
            # if self.path.endswith(".jpg"):
            #     mime_type = 'image/jpg'
            #     send_reply = True
            # if self.path.endswith(".gif"):
            #     mime_type = 'image/gif'
            #     send_reply = True
            # if self.path.endswith(".js"):
            #     mime_type = 'application/javascript'
            #     send_reply = True
            # if self.path.endswith(".css"):
            #     mime_type = 'text/css'
            #     send_reply = True

            if send_reply:
                # Open the static file requested and send it
                try:
                    #with open(os.curdir + os.sep + self.path) as f:
                    with open(self.path) as f:
                        self.send_response(200)
                        self.send_header("Content-type", mime_type)
                        self.end_headers()
                        self.wfile.write(f.read().encode("utf-8"))
                        f.close()

                except IOError:
                    self.send_error(404, "File Not Found: {}".format(self.path))
            return
        except Exception:
            logging.exception()

    def do_POST(self):
        try:
            if self.path == "/file_upload":
                self.handle_file_upload()
            if self.path == "/control":
                self.handle_mode_change()
            else:
                raise ValueError("Unexpected POST path: '{}'.".format(self.path))

        except Exception as e:
            print(e)
            self.send_error(418, "Upload failed - I'm a teapot")
    
    def handle_file_upload(self):
        ctype, pdict = cgi.parse_header(self.headers["content-type"])
        if ctype == "multipart/form-data":
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ=dict(
                    REQUEST_METHOD="POST",
                    CONTENT_TYPE=self.headers["Content-Type"]
                )
            )
            file_item = form["uploaded_file"]
            if not file_item.file:
                raise ValueError("form item is not a file")
            if file_item.done == -1:
                raise IOError("File upload was not completed...")
            name, ext = os.path.splitext(file_item.filename)
            if ext != ".png":
                raise ValueError("Unexpected extension: '{}'.".format(ext))

            with open("logo"+ext, "wb") as f:
                f.write(file_item.value)
            print("File upload was successful")

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write("File upload was successful".encode("utf-8"))

        else:
            raise ValueError("Unexpected ctype: '{}'.".format(ctype))

    def handle_mode_change(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ=dict(
                REQUEST_METHOD="POST",
                CONTENT_TYPE=self.headers["Content-Type"]
            )
        )
        mode = form.getfirst("mode")
        print(mode)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("Mode successfully changed to '{}'".format(mode).encode("utf-8"))