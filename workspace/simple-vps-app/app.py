from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers(); self.wfile.write(b'Halo dari VPS!')
HTTPServer(('0.0.0.0', 8000), H).serve_forever()
