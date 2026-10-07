import hashlib
import http.server
import json
import os
import pathlib
import shlex
import sqlite3
import ssl
import subprocess
import threading
import time
import urllib.request
import uuid

os.umask(0o077)
state = pathlib.Path('/root/xui-backups/20261006T191425Z-final-flush/acceptance')
state.mkdir(mode=0o700, exist_ok=True)
env = {}
for line in pathlib.Path('/etc/x-ui/install-result.env').read_text().splitlines():
    if '=' in line:
        key, value = line.split('=', 1)
        env[key] = shlex.split(value)[0] if value else ''
db = sqlite3.connect('file:/etc/x-ui/x-ui.db?mode=ro', uri=True)
settings = dict(db.execute('select key,value from settings'))
base = 'https://127.0.0.1:65000' + settings['webBasePath'].rstrip('/') + '/panel/api'
context = ssl._create_unverified_context()

def api(path, body=None):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization': 'Bearer ' + env['XUI_API_TOKEN'], 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, context=context, timeout=30) as response:
        value = json.load(response)
    if not value.get('success'):
        raise RuntimeError('API operation failed: ' + path)
    return value.get('obj')

email = 'codex-acceptance-' + uuid.uuid4().hex[:10]
client = {'id': str(uuid.uuid4()), 'email': email, 'enable': True, 'flow': '',
          'totalGB': 16 * 1048576, 'expiryTime': int((time.time() + 3600) * 1000),
          'limitIp': 0, 'subId': uuid.uuid4().hex[:16], 'tgId': 0, 'reset': 0}
result = {'checks': {}, 'synthetic_email': email}
process = None
server = None
created = False

def usage():
    row = db.execute('select up+down from client_traffics where email=?', (email,)).fetchone()
    return row[0] if row else 0

def counters():
    raw = subprocess.check_output(['/usr/local/x-ui/bin/xray-linux-amd64', 'api', 'statsquery',
        '--server=127.0.0.1:62789', '-pattern', 'user>>>' + email], stderr=subprocess.DEVNULL)
    return sum(int(item.get('value', 0)) for item in json.loads(raw).get('stat', []))

try:
    inbound = api('/inbounds/list')[0]
    api('/clients/add', {'client': client, 'inboundIds': [inbound['id']]})
    created = True
    time.sleep(6)
    stream = inbound['streamSettings']
    if isinstance(stream, str):
        stream = json.loads(stream)
    stream.pop('sockopt', None)
    config = {'log': {'loglevel': 'warning'},
        'inbounds': [{'listen': '127.0.0.1', 'port': 18888, 'protocol': 'socks', 'settings': {'udp': False}}],
        'outbounds': [{'protocol': 'vless', 'settings': {'vnext': [{'address': '127.0.0.1',
        'port': inbound['port'], 'users': [{'id': client['id'], 'encryption': 'none'}]}]}, 'streamSettings': stream}]}
    (state/'client.json').write_text(json.dumps(config))
    log = (state/'client.log').open('w')
    process = subprocess.Popen(['/usr/local/x-ui/bin/xray-linux-amd64', 'run', '-config', str(state/'client.json')], stdout=log, stderr=log)
    data = os.urandom(2 * 1048576)
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != '/blob':
                self.send_error(404); return
            self.send_response(200); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('139.100.204.34', 18889), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    time.sleep(2)
    def transfer():
        raw = subprocess.check_output(['curl', '--fail', '--silent', '--show-error', '--max-time', '20',
            '--noproxy', '', '--socks5-hostname', '127.0.0.1:18888', 'http://139.100.204.34:18889/blob'])
        assert hashlib.sha256(raw).digest() == hashlib.sha256(data).digest()
        return len(raw)
    result['bytes_received'] = transfer()
    snapshot = counters(); time.sleep(11)
    result['periodic_core_bytes'] = snapshot; result['periodic_panel_bytes'] = usage()
    result['checks']['periodic_accounting'] = usage() == snapshot and snapshot >= len(data)
    before_core = counters(); before_panel = usage()
    transfer(); final_core = counters()
    api('/server/restartXrayService', {})
    time.sleep(2)
    result['restart_core_delta'] = final_core-before_core
    result['restart_panel_delta'] = usage()-before_panel
    result['checks']['final_flush_restart'] = usage()-before_panel >= final_core-before_core
    result['checks']['restart_counters_empty'] = counters() == 0
    retained = usage(); time.sleep(6)
    result['checks']['no_double_accounting'] = usage() == retained
    def fresh_client():
        global process
        process.terminate()
        try: process.wait(timeout=5)
        except subprocess.TimeoutExpired: process.kill(); process.wait()
        process = subprocess.Popen(['/usr/local/x-ui/bin/xray-linux-amd64', 'run', '-config', str(state/'client.json')], stdout=log, stderr=log)
        time.sleep(2)
    fresh_client()
    before_core = counters(); before_panel = usage()
    transfer(); final_core = counters()
    subprocess.run(['systemctl', 'restart', 'x-ui'], check=True)
    time.sleep(6)
    result['shutdown_core_delta'] = final_core-before_core
    result['shutdown_panel_delta'] = usage()-before_panel
    result['checks']['final_flush_panel_shutdown'] = usage()-before_panel >= final_core-before_core
    result['checks']['panel_active_after_restart'] = subprocess.check_output(['systemctl', 'is-active', 'x-ui'], text=True).strip() == 'active'
    fresh_client()
    result['checks']['connection_after_panel_restart'] = transfer() == len(data)
    def denied():
        p = subprocess.run(['curl', '--fail', '--silent', '--max-time', '6', '--noproxy', '',
            '--socks5-hostname', '127.0.0.1:18888', 'http://139.100.204.34:18889/blob'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return p.returncode != 0
    client['totalGB'] = 1
    api('/clients/update/' + email, client)
    time.sleep(11)
    result['checks']['quota_disables_client'] = not bool(db.execute('select enable from client_traffics where email=?', (email,)).fetchone()[0])
    fresh_client()
    result['checks']['quota_rejects_connection'] = denied()
    client['totalGB'] = 16 * 1048576; client['enable'] = True; client['expiryTime'] = int((time.time()-60)*1000)
    api('/clients/update/' + email, client)
    time.sleep(11)
    result['checks']['expiry_disables_client'] = not bool(db.execute('select enable from client_traffics where email=?', (email,)).fetchone()[0])
    fresh_client()
    result['checks']['expiry_rejects_connection'] = denied()
finally:
    if process:
        process.terminate()
        try: process.wait(timeout=5)
        except subprocess.TimeoutExpired: process.kill(); process.wait()
    if server: server.shutdown(); server.server_close()
    if created:
        api('/clients/del/' + email, {})
        result['checks']['synthetic_client_removed'] = db.execute('select count(*) from client_traffics where email=?', (email,)).fetchone()[0] == 0
    (state/'result.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))
assert all(result['checks'].values()), 'Some remote checks failed'
