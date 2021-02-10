# if(__name__ == "__main__"):
#     import sys,os
    # sys.path.append(os.path.abspath("../"))

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os, sys, time
from datetime import datetime
from xml.etree import ElementTree
from xml.etree.ElementTree import ElementTree as ETree
from xml.dom import minidom 
from urllib.parse import unquote
import uuid, csv
import errno
import json
# from nools_gen import generate_nools
from pprint import pprint
import argparse, socket

print(sys.path)
from controllers.random import Random
from controllers.bkt import BKT
from controllers.dkt import DKT
from controllers.streak import Streak

def str_to_class(s):
    return getattr(sys.modules[__name__], s)

def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("",0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port
# 
def _read_data(handler):
    content_length = int(handler.headers['Content-Length']) # <--- Gets the size of data
    post_data = handler.rfile.read(content_length) # <--- Gets the data itself
    return post_data.decode('UTF-8')

def _print_and_resp(handler,outmode=sys.stdout):
    # content_length = int(handler.headers['Content-Length']) # <--- Gets the size of data
    # post_data = handler.rfile.read(content_length) # <--- Gets the data itself
    post_data = _read_data(handler)
    print(post_data,file=outmode)
    handler.send_response(200)
    handler.end_headers()

# session_default_dict =  {key: None for key in LOG_HEADERS.values()}
# output_file_path = None
# tool_dict = {}


active_controller = None

class OuterLoopHttpRequestHandler (SimpleHTTPRequestHandler):
    """http request handler with QUIT stopping the server"""

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        SimpleHTTPRequestHandler.end_headers(self)    

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        # self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'OPTIONS, NEW_STUDENT, NEXT_PROBLEM, POST')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # def do_INIT(self):
    #     post_data = _read_data(self)
    def do_NEXT_PROBLEM(self):
        global active_controller;
        print("NEXT PROBLEM", active_controller)
        post_data = _read_data(self)
        post_data = json.loads(post_data)

        if(active_controller is not None):
            nxt = active_controller.next_problem();
            print(nxt)

            self.send_response(200)
            self.send_header('Content-type', "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(nxt).encode("utf-8"))    
        else:
            self.send_response(400, "No Active controller.")




    def do_NEW_STUDENT(self):
        global active_controller;
        print("NEW STUDENT")
        post_data = _read_data(self)
        post_data = json.loads(post_data)
        # print(post_data)

        # if(active_controller is None):
        controller_class = str_to_class(post_data["outer_loop_type"])
        active_controller = controller_class()

        print(active_controller)

        active_controller.new_student(post_data["id"],post_data["problem_set"], post_data.get("outer_loop_args"))

        self.send_response(200)
        self.end_headers()   

    def do_POST (self):
        global active_controller;
        post_data = _read_data(self)
        post_data = json.loads(post_data)

        active_controller.update(post_data['selection'],
            post_data['reward'],post_data['action_type'])
    
        self.send_response(200)
        self.end_headers()

    def do_QUIT (self):
        _print_and_resp(self)
        self.server.stop = True
    
    def do_PRINT (self):
        _print_and_resp(self)

    def do_ERROR (self):
        _print_and_resp(self,sys.stderr)

    def log_message(self, format, *args):
        return
    def log_request(self,code='-', size='-'):
        return



class OuterLoopHttpServer (HTTPServer):
    """http server that reacts to self.stop flag"""

    def serve_forever (self):
        """Handle one request at a time until stopped."""
        self.stop = False
        while not self.stop:
            self.handle_request()

# assert len(sys.argv) > 1, "Error, correct usage: %s <port number>" % sys.argv[0]
# assert sys.argv[1].isdigit(), "invalid port %r" % sys.argv[1]
# port = int(sys.argv[1])


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Start a server that hosts the outerloop.')

    parser.add_argument('--host', default="localhost", metavar="<host>", dest='host',
        help="The port that the server will bind to.")
    parser.add_argument('--port', default=None, metavar="<port #>", dest='port', 
        help="The port that the server will bind to.")
    parser.add_argument('-a', '--controller' , default="Random", dest = "controller_name", metavar="<controller>",
        type=str, help="The name of the controller to be used.")

    try:
        args = parser.parse_args(argv)        
    except Exception:
        parser.print_usage()
        sys.exit()

    if(args.port is None):
        args.port = get_open_port()
    return args


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    print(args)

    server = OuterLoopHttpServer((args.host, int(args.port)), OuterLoopHttpRequestHandler)
    print("OUTERLOOP STARTED")
    server.serve_forever()
    print("IT DIED :(")
