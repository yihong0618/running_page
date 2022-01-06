#!/usr/bin/env python
"""
A basic authorization server.  Run this with your Strava Client ID and Client Secret and access from your
browser (because the Strava OAuth page uses javascript) in order to get a resulting access token.  That access
token can then be used to initialize a Client that can read (and/or write) data from the Strava API.

You must run this from a virtualenv that has stravalib installed.

Example Usage:

  (env) shell$ python -m stravalib.tests.auth_responder --port=8000 --client-id=123 --client-secret=deadbeefdeadbeefdeadbeefdeadbeefdeadbeef

  Then connect in your browser to http://localhost:8000/

  The redirected response (from Strava) will deliver a code that can be exchanged for a token.  The access token will be
  presented in the browser after the exchange.  Save this value into your config (e.g. into your test.ini) to run
  functional tests.
"""
from __future__ import unicode_literals, absolute_import, print_function

from six.moves.BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import argparse
from six.moves.urllib import parse as urlparse
import threading
import logging

import six

from stravalib import Client

class StravaAuthHTTPServer(HTTPServer):

    def __init__(self, server_address, RequestHandlerClass, client_id, client_secret, bind_and_activate=True):
        HTTPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate=bind_and_activate)
        self.logger = logging.getLogger('auth_server.http')
        self.client_id = client_id
        self.client_secret = client_secret
        self.listening_event = threading.Event()

    def serve_forever(self, *args, **kwargs):
        self.listening_event.set()
        return HTTPServer.serve_forever(self, *args, **kwargs)


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        request_path = self.path

        parsed_path = urlparse.urlparse(request_path)

        client = Client()

        if request_path.startswith('/authorization'):
            self.send_response(200)
            self.send_header(six.b("Content-type"), six.b("text/plain"))
            self.end_headers()

            self.wfile.write(six.b("Authorization Handler\n\n"))
            code = urlparse.parse_qs(parsed_path.query).get('code')
            if code:
                code = code[0]
                token_response = client.exchange_code_for_token(client_id=self.server.client_id,
                                                              client_secret=self.server.client_secret,
                                                              code=code)
                access_token = token_response['access_token']
                self.server.logger.info("Exchanged code {} for access token {}".format(code, access_token))
                self.wfile.write(six.b("Access Token: {}\n".format(access_token)))
            else:
                self.server.logger.error("No code param received.")
                self.wfile.write(six.b("ERROR: No code param recevied.\n"))
        else:
            url = client.authorization_url(client_id=self.server.client_id,
                                           redirect_uri='http://localhost:{}/authorization'.format(self.server.server_port))

            self.send_response(302)
            self.send_header(six.b("Content-type"), six.b("text/plain"))
            self.send_header(six.b('Location'), six.b(url))
            self.end_headers()
            self.wfile.write(six.b("Redirect to URL: {}\n".format(url)))


def main(port, client_id, client_secret):

    logging.basicConfig(level=logging.INFO, format='%(levelname)-8s %(message)s')

    logger = logging.getLogger('auth_responder')
    logger.info('Listening on localhost:%s' % port)

    server = StravaAuthHTTPServer(('', port), RequestHandler, client_id=client_id, client_secret=client_secret)
    server.serve_forever()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run a local web server to receive authorization responses from Strava.")

    parser.add_argument('-p', '--port', help='Which port to bind to',
                        action='store', type=int, default=8000)

    parser.add_argument('--client-id', help='Strava API Client ID',
                        action='store', required=True)
    parser.add_argument('--client-secret', help='Strava API Client Secret',
                        action='store', required=True)
    args = parser.parse_args()

    main(port=args.port, client_id=args.client_id, client_secret=args.client_secret)
