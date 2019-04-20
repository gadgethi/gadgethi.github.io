from http.server import HTTPServer, BaseHTTPRequestHandler

from io import BytesIO
from db_stuffs import handle_get, handle_post, local_db_test_init
import datetime

import json
from sys import argv
import doctest

def split_body(body, dictionary):
    """
    transform the http post to python dictionary

    >>> d = {}
    >>> d["form"] = {}
    >>> body = "way=1&lon=19.32940&len=2349"
    >>> split_body(body, d["form"])
    >>> print(d)
    {'form': {'way': '1', 'lon': '19.32940', 'len': '2349'}}
    """
    try:
        out = body.split('&')
    except:
        out = []

    for item in out:
        try:
            temp_list = item.split('=')
            dictionary[temp_list[0]] = temp_list[1]
        except IndexError as error:
            print("item: "+item+" doesn't use the query format")

def split_query_string(path, dictionary):
    """
    transform the http query string to python dictionary

    >>> d = {}
    >>> d["values"] = {}
    >>> query = "/?way=1&lon=19.32940&len=2349"
    >>> split_query_string(query, d)
    >>> print(d)
    {'values': {'way': '1', 'lon': '19.32940', 'len': '2349'}}
    """
    try:
        beginning = path.index('?')
        new_str = path[beginning+1:]
    except:
        return

    split_body(new_str, dictionary["values"])


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def preprocessing(self, method):
        """
        This formats the requests to a manageable
        form for the handle post and request functions
        """

        # get current time stamp
        timestamp = datetime.datetime.now()

        # create local database for testing
        local_db_test_init()

        # parse the request to match the 6.08 server request format
        d = {}
        d["method"] = method
        d["values"] = {}
        if method == "POST": 
            d["form"] = {}

        self.send_response(200)
        self.end_headers()

        split_query_string(self.path, d)
        d["args"] = list(d["values"].keys())

        return d, timestamp


    def do_GET(self):
        """
        entering point for the http get request
        """
        d, timestamp = self.preprocessing("GET")
        response = handle_get(d, timestamp)
        self.wfile.write(bytes(str(response), 'utf-8'))

    def do_POST(self):
        """
        entering point for the http post request
        """
        d, timestamp = self.preprocessing("POST")
        
        # read post body
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        split_body(body.decode("utf-8"), d["form"])

        response = handle_post(d, timestamp)
        self.wfile.write(bytes(str(response), 'utf-8'))

def server_run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8081):
    """
    Runs the server forever
    """
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting Database Server')
    httpd.serve_forever()

if __name__ == "__main__":
    doctest.testmod()   #This enable the doctest

    if len(argv) == 2:
        server_run(port=int(argv[1]))
    else:
        server_run()


