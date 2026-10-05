"""Reject non-public targets and revalidate every redirect for the public web app."""
import ipaddress
import socket
from urllib.parse import urlsplit
import requests
from slopradar.fetch import PageFetcher, BROWSER_HEADERS

def public_url(url):
    p=urlsplit(url)
    if p.scheme not in ('http','https') or not p.hostname or p.username or p.password or p.port not in (None,80,443):
        raise ValueError('Not a public web URL')
    addresses=socket.getaddrinfo(p.hostname,p.port or (443 if p.scheme=='https' else 80),type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Non-public address')
    return url

# The actual TCP destination must be the checked IP, not a second DNS lookup.
class PinnedAdapter(requests.adapters.HTTPAdapter):
    def get_connection_with_tls_context(self, request, verify, proxies=None, cert=None):
        from urllib3 import HTTPConnectionPool, HTTPSConnectionPool
        p=urlsplit(request.url);public_url(request.url)
        address=socket.getaddrinfo(p.hostname,p.port or (443 if p.scheme=='https' else 80),type=socket.SOCK_STREAM)[0][4][0]
        if not ipaddress.ip_address(address).is_global:
            raise ValueError('Non-public address')
        request.headers['Host']=p.netloc
        if p.scheme=='https':
            return self.poolmanager.connection_from_host(address,p.port or 443,scheme='https',pool_kwargs={'assert_hostname':p.hostname,'server_hostname':p.hostname,'cert_reqs':'CERT_REQUIRED'})
        return self.poolmanager.connection_from_host(address,p.port or 80,scheme='http')

class PublicSession(requests.Session):
    def request(self, method, url, **kwargs):
        public_url(url)
        # Requests validates redirect targets via get_redirect_target below.
        return super().request(method,url,**kwargs)
    def get_redirect_target(self, response):
        target=super().get_redirect_target(response)
        if target:
            from urllib.parse import urljoin
            public_url(urljoin(response.url,target))
        return target

class PublicPageFetcher(PageFetcher):
    def __init__(self, **kwargs):
        session=PublicSession();session.trust_env=False;session.mount('http://',PinnedAdapter());session.mount('https://',PinnedAdapter())
        super().__init__(session=session,**kwargs)
    def fetch(self,url):
        from slopradar.fetch import FetchedPage
        try:
            return super().fetch(url)
        except (ValueError,socket.gaierror):
            return FetchedPage(url=url,ok=False,error='Not a reachable public web page')
