import os
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from webapp.service import ScanService, ScanError, clean_query

from werkzeug.middleware.proxy_fix import ProxyFix
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config['MAX_CONTENT_LENGTH'] = 4096
service = ScanService()

@app.after_request
def headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Cache-Control'] = 'no-store' if request.path.startswith('/api') else 'public, max-age=300'
    return response

@app.get('/')
def home():
    return render_template('index.html')

@app.get('/health')
def health():
    return jsonify(status='ok')

@app.post('/api/scan')
def scan():
    if request.headers.get('Origin') and request.headers['Origin'].rstrip('/') != request.host_url.rstrip('/'):
        return jsonify(error='Search from this page.'), 403
    try:
        body=request.get_json(silent=True) or {}
        if not isinstance(body, dict):
            raise ScanError('Enter a search term.', 400)
        query=clean_query(body.get('query'))
        return jsonify(service.scan(query))
    except ScanError as exc:
        return jsonify(error=str(exc)), exc.status
    except Exception:
        # Upstream/network errors may contain secrets. Never echo them.
        return jsonify(error='Search could not finish. Try a saved result or come back later.'), 503

if __name__ == '__main__':
    app.run(port=int(os.environ.get('PORT','8000')))
