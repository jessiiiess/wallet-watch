"""Bounded resumable cloud collection. Standard library; no LLM API calls."""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ORIGIN = os.environ.get('SITE_ORIGIN', 'https://jessie-wallet-watch.proudbuttercup1.chatgpt.site').rstrip('/')
if urllib.parse.urlparse(ORIGIN).scheme != 'https':
    raise SystemExit('SITE_ORIGIN must use HTTPS')
_token = None
_token_at = 0

class CollectionError(Exception):
    pass

def request_json(url, method='GET', token=None):
    request = urllib.request.Request(url, data=b'{}' if method=='POST' else None, method=method,
        headers={'Authorization': 'Bearer '+token} if token else {})
    try:
        with urllib.request.urlopen(request, timeout=100) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise CollectionError('HTTP_'+str(exc.code)) from None
    except (OSError, ValueError):
        raise CollectionError('NETWORK_OR_JSON_ERROR') from None

def credential():
    global _token, _token_at
    if os.getenv('SCHEDULER_TOKEN'):
        return os.environ['SCHEDULER_TOKEN']
    if _token and time.monotonic()-_token_at<180:
        return _token
    base=os.environ.get('ACTIONS_ID_TOKEN_REQUEST_URL')
    auth=os.environ.get('ACTIONS_ID_TOKEN_REQUEST_TOKEN')
    if not base or not auth:
        raise CollectionError('NO_SCHEDULER_IDENTITY')
    url=base+('&' if '?' in base else '?')+urllib.parse.urlencode({'audience':ORIGIN})
    result=request_json(url,token=auth)
    _token=result['value'];_token_at=time.monotonic()
    return _token

def run(max_steps=1500, max_seconds=2400):
    started=time.monotonic()
    for step in range(max_steps):
        if time.monotonic()-started>max_seconds:
            raise CollectionError('TIME_BUDGET_REACHED_CURSOR_SAVED')
        result=None
        for attempt in range(3):
            try:
                result=request_json(ORIGIN+'/api/refresh','POST',credential())
                break
            except CollectionError as exc:
                if str(exc) in ('HTTP_401','HTTP_403') or attempt==2:
                    raise
                time.sleep(2**attempt)
        # Server replies are allowlisted; never print credentials or request URLs.
        safe={k:result[k] for k in ('state','phase','records','completedDirections','totalDirections','code','updatedAt','caughtUp') if k in result}
        if step%20==0 or result['state'] in ('failed','complete','started'):
            print(json.dumps({'step':step,**safe},ensure_ascii=False),flush=True)
        if result['state']=='failed':
            raise CollectionError(result.get('code','COLLECTION_FAILED'))
        if result['state']=='busy':
            time.sleep(5)
            continue
        if result['state']=='complete' and result.get('caughtUp',True):
            public=request_json(ORIGIN+'/api/data')
            if not public.get('updatedAt') or public['updatedAt']!=result['updatedAt']:
                raise CollectionError('PUBLISHED_READBACK_MISMATCH')
            print(json.dumps({'verified':True,'updatedAt':public['updatedAt'],'transfers':public['totalTransfers'],'events':public['totalEvents']},ensure_ascii=False))
            return public
    raise CollectionError('STEP_BUDGET_REACHED_CURSOR_SAVED')

if __name__=='__main__':
    try:
        run()
    except CollectionError as exc:
        print('Collection stopped: '+str(exc),file=sys.stderr)
        sys.exit(1)
