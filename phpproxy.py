#!/usr/bin/python2

# bind socket to following address
# there is no access control, if someone can connect to
# phpproxy client, he can use it
# by default bind to 127.0.0.1 (localhost) so only programs
# on local computer can connect
#localhost = '127.0.0.1'
localhost = ''
# or bind to private network address
#localhost = '192.168.0.1'
# to allow anyone to connect use empty host
#localhost = ''

# port proxy will listen on
localport = 80

# proxy server module located here
# if website is an ip based (not name-based virtual host) use
# ip address for better performance
# if unsure use full hostname
phpproxy = 'https://malu.me/phpproxy.php'

# set this if you have proxy between your box and phpproxy.php
#proxy = 'http://127.0.0.1:5865/'
#proxy = 'http://192.168.0.254:8080/'
# or no proxy
proxy = None

useragent = 'PHPProxy; -1bit; Python/PHP'

# settings above can be overriden without editing script
# by placing file 'phpproxy.py.conf' in current working
# directory (usefull when phpproxy.py is distributed as
# standalone binary that do not require Python, for Win32
# platform, for example)
config       = 'phpproxy.py.conf'
# or absolute path
#config      = '/etc/phpproxy.py.conf'
# disable external config
#config = None


##############################

import SocketServer
import re
import urllib
import sys

class ProxyHandler(SocketServer.StreamRequestHandler):
    allow_reuse_address = 1

    def handle(self):
        req, body, cl, req_len, read_len = '', 0, 0, 0, 4096
        try:
            while 1:
                if not body:
                    line = self.rfile.readline(read_len)
                    if line == '':                                 
                        # send it anyway..
                        self.send_req(req)
                        return
                    #if line[0:17].lower() == 'proxy-connection:':
                    #    req += "Connection: close\r\n"
                    #    continue
                    req += line
                    if not cl:
                        t = re.compile('^Content-Length: (\d+)', re.I).search(line)
                        if t is not None:
                            cl = int(t.group(1))
                            continue
                    if line == "\015\012" or line == "\012":
                        if not cl:
                            self.send_req(req)
                            return
                        else:
                            body = 1
                            read_len = cl
                else:
                    buf = self.rfile.read(read_len)
                    req += buf
                    req_len += len(buf)
                    read_len = cl - req_len
                    if req_len >= cl:
                        self.send_req(req)
                        return
        except IOError:
            return

    def send_req(self, req):
        #print req
        if req == '':
            return
        ua = urllib.FancyURLopener(proxies)
        ua.addheaders = [('User-Agent', useragent)]
        r = ua.open(phpproxy, urllib.urlencode({'req': req}))
        while 1:
            c = r.read(2048)
            if c == '': break
            self.wfile.write(c)
        self.wfile.close()

proxies = {}
if proxy is not None: proxies['http'] = proxy
if config is not None:
    try:
        execfile(config)
    except:
        print "Can't parse config file '%s': %s" % (config, sys.exc_info()[1])
        print "Continuing with internal config"

server = SocketServer.ThreadingTCPServer((localhost, localport), ProxyHandler)
print 'proxy server ready..'
server.serve_forever()
