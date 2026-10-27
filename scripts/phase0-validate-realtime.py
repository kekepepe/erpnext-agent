#!/usr/bin/env python3
"""Check native authenticated Socket.IO namespace and origin/auth rejection.

Uses Engine.IO polling via stdlib HTTP, not browser automation. Session/engine
identifiers and cookies never printed, persisted or stored in public fixtures.
"""
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from phase0_api import ERPNextAPI,validate_disposable_url

BASE=validate_disposable_url(os.environ.get('PHASE0_BASE_URL','http://localhost:8080'))
PATH='/socket.io/?EIO=4&transport=polling'
ORIGIN=BASE


def connection(opener, expected):
    def request(method,body=None,sid=None,origin=ORIGIN):
        path=PATH+(('&sid='+urllib.parse.quote(sid)) if sid else '')
        headers={'Origin':origin,'Content-Type':'text/plain;charset=UTF-8'}
        req=urllib.request.Request(BASE+path,data=body.encode() if body is not None else None,headers=headers,method=method)
        with opener.open(req,timeout=15) as response:return response.read().decode()
    first=request('GET')
    if not first.startswith('0'):raise RuntimeError('Invalid native Engine.IO handshake')
    sid=json.loads(first[1:])['sid']
    try:
        request('POST','40/frontend,',sid)
        found=False
        for _ in range(5):
            frames=request('GET',sid=sid).split('\x1e')
            for frame in frames:
                if frame=='2':request('POST','3',sid)
                if frame.startswith(expected+'/frontend,'):found=True
                elif frame.startswith(('40/frontend,','44/frontend,')):raise RuntimeError('Unexpected authentication result')
            if found:break
        if not found:raise RuntimeError('Native namespace result not received')
    finally:
        request('POST','1',sid)


def main():
    api=ERPNextAPI(BASE);api.login('Administrator',os.environ.get('PHASE0_PASSWORD','admin'))
    connection(api.opener,'40')
    try:
        req=urllib.request.Request(BASE+PATH,headers={'Origin':'http://example.invalid'})
        api.opener.open(req,timeout=10)
    except urllib.error.HTTPError as error:
        if error.code!=403:raise
    else:raise RuntimeError('Foreign origin unexpectedly accepted')
    connection(urllib.request.build_opener(),'44')
    print(json.dumps({'namespace':'frontend','authenticated_connect':'PASS','foreign_origin_403':'PASS','missing_auth_rejected':'PASS'},sort_keys=True))

if __name__=='__main__':main()
