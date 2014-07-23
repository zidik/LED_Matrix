__author__ = 'Mark'

from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import cgi
import logging
import threading

from game_controller import GameController
from games import CatchColorsMultiplayer #For configuring


class MatrixWebserver(threading.Thread):
    def __init__(self, game_controller, address, port):
        super().__init__()
        self.name = "Server thread"
        self.server = HTTPServer((address, port), MyHTTPRequestHandler)
        MyHTTPRequestHandler.game_controller = game_controller

    def run(self):
        logging.info("Server started.")
        self.server.serve_forever()

    def join(self, timeout=None):
        self.server.shutdown()
        logging.info("Server stopped.")
        super().join(timeout)


class MyHTTPRequestHandler(BaseHTTPRequestHandler):
    game_controller = None

    def do_GET(self):
        try:
            response = ""
            if self.path == "/":
                # noinspection PyAttributeOutsideInit
                self.path = "index.html"

            if self.path.endswith(".html"):
                mime_type = 'text/html'
            # if self.path.endswith(".jpg"):
            # mime_type = 'image/jpg'
            # if self.path.endswith(".gif"):
            # mime_type = 'image/gif'
            elif self.path.endswith(".js"):
                mime_type = 'application/javascript'
            elif self.path.endswith(".css"):
                mime_type = 'text/css'
            else:
                self.send_error(404, "File Not Found: {} (ext. not supported)".format(self.path))
                return

            # Open the static file requested and send it
            try:
                with open(os.curdir + os.sep + "public_http" + os.sep + self.path) as f:
                    response = f.read()
            except IOError:
                self.send_error(404, "File Not Found: {}".format(self.path))

            # Successful
            self.send_response(200)
            self.send_header("Content-type", mime_type)
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))
        except Exception as e:
            # Unsuccessful
            logging.exception("Handling GET request produced exception.")
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write("Error: {}".format(e).encode("utf-8"))


    def do_POST(self):
        try:
            if self.path == "/file_upload":
                response = self.handle_file_upload()
            elif self.path == "/mode_change":
                response = self.handle_mode_change()
            elif self.path == "/power_toggle":
                response = self.handle_power_toggle()
            else:
                raise ValueError("Unexpected POST path: '{}'.".format(self.path))

            # Successful
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))
        except Exception as e:
            # Unsuccessful
            logging.exception("Handling POST request produced exception.")
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write("Error: {}".format(e).encode("utf-8"))

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

            with open("logo" + ext, "wb") as f:
                f.write(file_item.value)
            response = "File upload was successful"

        else:
            raise ValueError("Unexpected ctype: '{}'.".format(ctype))

        return response

    def handle_mode_change(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ=dict(
                REQUEST_METHOD="POST",
                CONTENT_TYPE=self.headers["Content-Type"]
            )
        )

        response = ""

        mode = form.getfirst("mode")
        if mode is not None and mode != "nothing":
            MyHTTPRequestHandler.game_controller.set_game_mode(GameController.Mode[mode])
            response += "Mode successfully changed to '{}'. \n".format(mode)

        catch_colors_players = form.getfirst("catch_colors_players")
        if catch_colors_players is not None and catch_colors_players != "nothing":
            CatchColorsMultiplayer.number_of_players = int(catch_colors_players)
            self.game_controller.reset_game()
            response += "Players successfully changed to '{}'. \n".format(CatchColorsMultiplayer.number_of_players)

        return response

    def handle_power_toggle(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ=dict(
                REQUEST_METHOD="POST",
                CONTENT_TYPE=self.headers["Content-Type"]
            )
        )
        power = form.getfirst("power")

        if power == "on":
            MyHTTPRequestHandler.game_controller.matrix_controller.start()
        elif power == "off":
            MyHTTPRequestHandler.game_controller.matrix_controller.stop()
        else:
            raise ValueError("unknown power value: '{}'".format(power))

        response = "Power turned {}.".format(power)
        return response
