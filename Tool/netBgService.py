from wsgiref.simple_server import make_server, WSGIServer
import webbrowser
def application(environ, start_response):
    print("Hello world!")
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [b'<h1>Hello, web!</h1>']
    from io import StringIO
    stdout = StringIO()
    print("Hello world!", file=stdout)
    print(file=stdout)
    h = sorted(environ.items())
    for k,v in h:
        print(k,'=',repr(v), file=stdout)
    start_response("200 OK", [('Content-Type','text/plain; charset=utf-8')])
    return [stdout.getvalue().encode("utf-8")]

TEST = False
if __name__ == '__main__':
    httpd :WSGIServer = make_server(host='', port=8001, app=application)
    sa = httpd.socket.getsockname()
    if TEST:
        print("Serving HTTP on", sa[0], "port", sa[1], "...")
        webbrowser.open('http://localhost:8001/xyz?abc')
        httpd.handle_request()  # serve one request, then exit
    else:
        httpd.serve_forever()
