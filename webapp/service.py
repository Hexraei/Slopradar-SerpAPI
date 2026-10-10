"""Durable global budget and cache. No browser ever receives account credentials."""
import hashlib
import json
import os
from datetime import datetime, timezone

import psycopg2
import requests

from webapp.safe_fetch import PublicPageFetcher
from slopradar.pipeline import run_radar, NicheReport, PageReport
from dataclasses import fields
from slopradar.serp import SerpApiClient
from slopradar.html_report import to_html

SCHEMA = '''
CREATE TABLE IF NOT EXISTS slop_cache (key text PRIMARY KEY, report jsonb NOT NULL, html text NOT NULL, created_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS slop_spend (day date PRIMARY KEY, attempts integer NOT NULL CHECK(attempts >= 0));
'''

class ScanError(Exception):
    def __init__(self, message, status=503):
        self.status = status
        super().__init__(message)

def clean_query(value):
    if not isinstance(value, str):
        raise ScanError('Enter a search term.', 400)
    query = ' '.join(value.split())
    if not 2 <= len(query) <= 120 or any(ord(c) < 32 for c in query):
        raise ScanError('Use 2-120 characters.', 400)
    return query

class ScanService:
    def scan(self, query):
        query = clean_query(query)
        key = hashlib.sha256(('us:en:v1:'+query.casefold()).encode()).hexdigest()
        db_url = os.environ.get('DATABASE_URL')
        api_key = os.environ.get('SERPAPI_API_KEY')
        if not db_url or not api_key:
            raise ScanError('Live search is not configured yet.')
        conn = psycopg2.connect(db_url, connect_timeout=8, sslmode='require')
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = '15000ms'")
                cur.execute(SCHEMA)
                
                # All public scans serialize across processes and deployments.
                # No counter reset on restart and no race between cache and spend.
                cur.execute('SELECT pg_try_advisory_lock(74309182)')
                if not cur.fetchone()[0]:
                    raise ScanError('Another search is running. Try again in a moment.', 429)
                cur.execute("DELETE FROM slop_cache WHERE created_at < now() - interval '24 hours'")
                cur.execute("DELETE FROM slop_spend WHERE day < current_date - 31")
                cur.execute('SELECT report, html, created_at FROM slop_cache WHERE key=%s AND created_at > now() - interval \'24 hours\'', (key,))
                cached = cur.fetchone()
                if cached:
                    data = cached[0]
                    report = NicheReport(**{f.name: data[f.name] for f in fields(NicheReport) if f.name in data and f.name != 'pages'}, pages=[PageReport(**p) for p in data['pages']])
                    return {'report':report.to_dict(), 'html':to_html(report), 'cached':True, 'scanned_at':cached[2].isoformat()}
                day = datetime.now(timezone.utc).date()
                cur.execute('SELECT attempts FROM slop_spend WHERE day=%s',(day,))
                row = cur.fetchone(); used = row[0] if row else 0
                cap = min(20, max(0, int(os.environ.get('DAILY_SEARCH_CAP','20'))))
                if used >= cap:
                    raise ScanError('Today\'s live-search limit is reached. Saved results still work.', 429)
                account = requests.get('https://serpapi.com/account.json', params={'api_key':api_key}, timeout=10)
                if account.status_code != 200:
                    raise ScanError('Could not verify the search allowance. No search was run.')
                balance = account.json().get('total_searches_left')
                # Extra five-credit cushion for concurrent use outside this app.
                if not isinstance(balance,(int,float)) or balance <= 105:
                    raise ScanError('The reserved search allowance is protected. No search was run.', 429)
                # Count attempts BEFORE calling upstream. An uncertain timeout never retries.
                cur.execute('INSERT INTO slop_spend(day,attempts) VALUES(%s,1) ON CONFLICT(day) DO UPDATE SET attempts=slop_spend.attempts+1',(day,))
                client = SerpApiClient(cache_dir=None)
                fetcher=PublicPageFetcher(timeout=8)
                try:
                    report = run_radar(query, search=lambda q: client.search(q,gl='us',hl='en'),fetcher=fetcher,queries=1,max_results=8,serp_stats=lambda:{'calls':client.calls_made,'cache_hits':client.cache_hits})
                finally:
                    fetcher.session.close()
                data = report.to_dict();markup = to_html(report)
                cur.execute('INSERT INTO slop_cache(key,report,html) VALUES(%s,%s::jsonb,%s) ON CONFLICT(key) DO UPDATE SET report=EXCLUDED.report,html=EXCLUDED.html,created_at=now()', (key,json.dumps(data),markup))
                return {'report':data,'html':markup,'cached':False,'scanned_at':report.generated_at}
        finally:
            # Closing releases the session advisory lock even on failure.
            conn.close()
