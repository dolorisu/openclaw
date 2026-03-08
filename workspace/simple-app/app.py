from http.server import HTTPServer, BaseHTTPRequestHandler
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header("Content-type","text/plain; charset=utf-8"); self.end_headers(); self.wfile.write(b"Halo dari VPS!\n")
HTTPServer(("0.0.0.0", 18080), H).serve_forever()
