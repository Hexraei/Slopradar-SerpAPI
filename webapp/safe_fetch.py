"""Reject non-public targets and revalidate every redirect for the public web app."""
import ipaddress
import socket
from urllib.parse import urlsplit
import requests
from slopradar.fetch import PageFetcher, BROWSER_HEADERS, USER_AGENT

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

    def allowed(self, url):
        """Read robots with the same size and destination limits as pages."""
        from urllib import robotparser
        from urllib.parse import urlsplit
        p=urlsplit(url);base=f'{p.scheme}://{p.netloc}'
        if base not in self._robots:
            try:
                with self.session.get(base+'/robots.txt',timeout=self.timeout,stream=True) as response:
                    if response.status_code==200:
                        chunks=[];size=0
                        for chunk in response.iter_content(8192):
                            size+=len(chunk)
                            if size>256_000:break
                            chunks.append(chunk)
                        else:
                            rp=robotparser.RobotFileParser();rp.parse(b''.join(chunks).decode('utf-8',errors='replace').splitlines());self._robots[base]=rp
                            return rp.can_fetch(USER_AGENT,url)
                    self._robots[base]=None
            except requests.RequestException:self._robots[base]=None
        rp=self._robots[base]
        return True if rp is None else rp.can_fetch(USER_AGENT,url)
