import urllib.request

try:
    resp = urllib.request.urlopen('http://localhost:8501')
    print('STATUS', resp.status)
    html = resp.read(200).decode('utf-8', errors='ignore')
    print('BODY START', html)
except Exception as e:
    print('ERROR', repr(e))
