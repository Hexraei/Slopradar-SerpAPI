import pytest
from webapp.app import app
from webapp.service import clean_query, ScanError
from webapp.safe_fetch import public_url

@pytest.mark.parametrize('value',[None,1,'','x','x'*121,{'query':'test'}])
def test_query_validation(value):
    with pytest.raises(ScanError):clean_query(value)

def test_query_normalization():
    assert clean_query(' AI  writing\n tools ')=='AI writing tools'

@pytest.mark.parametrize('url',['file:///etc/passwd','http://localhost/','http://127.0.0.1/','http://169.254.169.254/','http://[::1]/','http://user:pass@example.com/','https://example.com:444/'])
def test_nonpublic_fetch_targets_rejected(url):
    with pytest.raises(ValueError):public_url(url)

def test_home_and_health():
    c=app.test_client()
    assert c.get('/').status_code==200
    assert c.get('/health').json=={'status':'ok'}
    assert b'SERPAPI_API_KEY' not in c.get('/').data

def test_bad_scan_inputs_do_not_run(monkeypatch):
    monkeypatch.setattr('webapp.app.service.scan',lambda _:pytest.fail('must not run'))
    c=app.test_client()
    assert c.post('/api/scan',json={'query':'x'}).status_code==400
    assert c.post('/api/scan',json={'query':'valid'},headers={'Origin':'https://evil.invalid'}).status_code==403

def test_scan_errors_never_echo_credentials(monkeypatch):
    def fail(_):raise RuntimeError('api_key=SECRET')
    monkeypatch.setattr('webapp.app.service.scan',fail)
    r=app.test_client().post('/api/scan',json={'query':'writing tools'})
    assert r.status_code==503 and b'SECRET' not in r.data

def test_pinned_adapter_rejects_rebinding(monkeypatch):
    import socket,requests
    from webapp.safe_fetch import PinnedAdapter
    calls=iter([[(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',443))],[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))]])
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**k:next(calls))
    req=requests.Request('GET','https://example.com/').prepare()
    with pytest.raises(ValueError):PinnedAdapter().get_connection_with_tls_context(req,True)

def test_reserve_guard_no_search_below_reserve(monkeypatch):
    import webapp.service as svc
    monkeypatch.setenv('DATABASE_URL','unused');monkeypatch.setenv('SERPAPI_API_KEY','SECRET')
    class Cur:
        def __init__(self):self.stage=0;self.commands=[]
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def execute(self,q,args=None):self.commands.append(q)
        def fetchone(self):
            self.stage+=1
            return {1:(True,),2:None,3:(0,)}[self.stage]
    cur=Cur()
    class Conn:
        def cursor(self):return cur
        def close(self):pass
    monkeypatch.setattr(svc.psycopg2,'connect',lambda *a,**k:Conn())
    class Account:
        status_code=200
        def json(self):return {'total_searches_left':105}
    monkeypatch.setattr(svc.requests,'get',lambda *a,**k:Account())
    monkeypatch.setattr(svc,'SerpApiClient',lambda **k:pytest.fail('no spend'))
    with pytest.raises(ScanError):svc.ScanService().scan('test query')
    assert not any('INSERT INTO slop_spend' in q for q in cur.commands)

def test_daily_cap_counts_uncertain_attempts(monkeypatch):
    import webapp.service as svc
    monkeypatch.setenv('DATABASE_URL','unused');monkeypatch.setenv('SERPAPI_API_KEY','SECRET')
    class Cur:
        def __init__(self):self.stage=0;self.commands=[]
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def execute(self,q,args=None):self.commands.append(q)
        def fetchone(self):
            self.stage+=1
            return {1:(True,),2:None,3:(20,)}[self.stage]
    cur=Cur()
    class Conn:
        def cursor(self):return cur
        def close(self):pass
    monkeypatch.setattr(svc.psycopg2,'connect',lambda *a,**k:Conn())
    monkeypatch.setattr(svc.requests,'get',lambda *a,**k:pytest.fail('cap before upstream'))
    with pytest.raises(ScanError):svc.ScanService().scan('test query')

def test_cache_precedes_upstream_and_budget(monkeypatch):
    import webapp.service as svc
    from datetime import datetime,timezone
    monkeypatch.setenv('DATABASE_URL','unused');monkeypatch.setenv('SERPAPI_API_KEY','SECRET')
    class Cur:
        def __init__(self):self.stage=0
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def execute(self,q,args=None):pass
        def fetchone(self):
            self.stage+=1
            return (True,) if self.stage==1 else ({'query':'cached'},'<html>cached</html>',datetime.now(timezone.utc))
    class Conn:
        closed=False
        def cursor(self):return Cur()
        def close(self):self.closed=True
    conn=Conn();monkeypatch.setattr(svc.psycopg2,'connect',lambda *a,**k:conn)
    monkeypatch.setattr(svc.requests,'get',lambda *a,**k:pytest.fail('cache must not spend'))
    assert svc.ScanService().scan('TEST QUERY')['cached']
    assert conn.closed

def test_lock_contention_never_spends(monkeypatch):
    import webapp.service as svc
    monkeypatch.setenv('DATABASE_URL','unused');monkeypatch.setenv('SERPAPI_API_KEY','SECRET')
    class Cur:
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def execute(self,q,args=None):pass
        def fetchone(self):return (False,)
    class Conn:
        closed=False
        def cursor(self):return Cur()
        def close(self):self.closed=True
    conn=Conn();monkeypatch.setattr(svc.psycopg2,'connect',lambda *a,**k:conn)
    monkeypatch.setattr(svc.requests,'get',lambda *a,**k:pytest.fail('contention must not spend'))
    with pytest.raises(ScanError) as e:svc.ScanService().scan('test query')
    assert e.value.status==429 and conn.closed
