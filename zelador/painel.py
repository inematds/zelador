"""Painel: formulário para ler a pauta e decidir cada proposta (aprovar / recusar / analisar / adiar).

GET  /               a pauta mais recente com as decisões já tomadas
POST /api/decidir    {id, decisao, nota}
POST /api/fechar     aprovadas + 'analisar' vão para o arquivo de pendências e o aviso manda o placar
Escuta só em 127.0.0.1 por padrão; outros endereços (ex.: VPN) entram por `painel.enderecos`.
"""
import datetime as dt
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import avisar, config, controle

HTML = Path(__file__).with_name('painel.html')
VALIDAS = {'aprovar', 'recusar', 'analisar', 'adiar', ''}
TRAVA = threading.Lock()


def ler(p, padrao):
    return json.loads(p.read_text()) if p.is_file() else padrao


def pauta_atual(cfg):
    ps = sorted(config.dados(cfg, 'pautas').glob('*.json'))
    return ler(ps[-1], {}) if ps else {'semana': '-', 'itens': []}


def arquivo_pendencias(cfg):
    achados = controle.achar(cfg, 'pendencias')
    if achados:
        return achados[0]
    p = config.hub(cfg) / 'PENDENCIAS.md'
    if not p.exists():
        p.write_text('# Pendências\n\nMais recente no topo. Ao resolver, marcar [x] com a data.\n')
    return p


def fechar(cfg):
    pauta = pauta_atual(cfg)
    arq_dec = config.dados(cfg) / 'decisoes.json'
    dec = ler(arq_dec, {})
    por_id = {i['id']: i for i in pauta.get('itens', [])}
    envio = [(k, d) for k, d in dec.items() if d.get('semana') == pauta['semana']
             and d['decisao'] in ('aprovar', 'analisar') and not d.get('enviado')]
    if not envio:
        return {'ok': True, 'enviados': 0, 'msg': 'nada novo para enviar'}
    hoje = dt.date.today()
    nome = {'aprovar': 'Fazer', 'analisar': 'Analisar antes'}
    linhas = [f"- [ ] **{hoje:%d/%m/%Y} — Pauta semanal {pauta['semana']}: "
              f"{sum(d['decisao'] == 'aprovar' for _, d in envio)} aprovada(s), "
              f"{sum(d['decisao'] == 'analisar' for _, d in envio)} para analisar** (zelador)."]
    for k, d in sorted(envio, key=lambda x: x[1]['decisao']):
        it = por_id.get(k, d)
        nota = f" Nota: {d['nota']}" if d.get('nota') else ''
        linhas.append(f"  - {nome[d['decisao']]} [{it.get('fonte', '')}] {it.get('titulo', '')[:160]} — "
                      f"{it.get('proposta', '')[:240]}{nota}")
    p = arquivo_pendencias(cfg)
    cab, _, resto = p.read_text().partition('\n')
    p.write_text(cab + '\n\n' + '\n'.join(linhas) + '\n' + resto)
    for _, d in envio:
        d['enviado'] = hoje.isoformat()
    arq_dec.write_text(json.dumps(dec, ensure_ascii=False, indent=1))
    todas = [d for d in dec.values() if d.get('semana') == pauta['semana']]
    r = {x: sum(d['decisao'] == x for d in todas) for x in ('aprovar', 'recusar', 'analisar', 'adiar')}
    avisar.avisar(cfg, f"📋 Pauta {pauta['semana']} fechada: {r['aprovar']} aprovada(s), {r['analisar']} para analisar, "
                       f"{r['recusar']} recusada(s), {r['adiar']} adiada(s). Entrou em {p}.")
    return {'ok': True, 'enviados': len(envio), 'arquivo': str(p)}


def decidir(cfg, corpo):
    pauta = pauta_atual(cfg)
    it = next((i for i in pauta.get('itens', []) if i['id'] == corpo.get('id')), None)
    if not it or corpo.get('decisao') not in VALIDAS:
        return None
    arq = config.dados(cfg) / 'decisoes.json'
    dec = ler(arq, {})
    if corpo['decisao'] == '' and not corpo.get('nota'):
        dec.pop(it['id'], None)
    else:
        ant = dec.get(it['id'], {})
        dec[it['id']] = {'decisao': corpo['decisao'], 'nota': str(corpo.get('nota', ''))[:2000],
                         'quando': dt.datetime.now().isoformat(timespec='minutes'), 'semana': pauta['semana'],
                         'fonte': it['fonte'], 'titulo': it['titulo'], 'proposta': it['proposta'],
                         **({'enviado': ant['enviado']} if ant.get('enviado') and ant.get('decisao') == corpo['decisao'] else {})}
    arq.write_text(json.dumps(dec, ensure_ascii=False, indent=1))
    return {'ok': True}


def fabrica(cfg):
    class H(BaseHTTPRequestHandler):
        def _resp(self, corpo, tipo, code=200):
            self.send_response(code)
            self.send_header('Content-Type', tipo)
            self.send_header('Content-Length', str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def _json(self, obj, code=200):
            self._resp(json.dumps(obj, ensure_ascii=False).encode(), 'application/json; charset=utf-8', code)

        def do_GET(self):
            if self.path not in ('/', '/index.html'):
                return self._json({'erro': 'não existe'}, 404)
            dados = json.dumps({'pauta': pauta_atual(cfg), 'decisoes': ler(config.dados(cfg) / 'decisoes.json', {})},
                               ensure_ascii=False)
            self._resp(HTML.read_text().replace('__DADOS__', dados.replace('</', '<\\/')).encode(),
                       'text/html; charset=utf-8')

        def do_POST(self):
            try:
                corpo = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0) or 0)) or b'{}')
            except ValueError:
                return self._json({'erro': 'json inválido'}, 400)
            with TRAVA:
                if self.path == '/api/decidir':
                    r = decidir(cfg, corpo)
                    return self._json(r or {'erro': 'item ou decisão inválida'}, 200 if r else 400)
                if self.path == '/api/fechar':
                    return self._json(fechar(cfg))
            self._json({'erro': 'não existe'}, 404)

        def log_message(self, *a):
            pass
    return H


def servir(cfg):
    porta, H, servidores = cfg['painel']['porta'], fabrica(cfg), []
    for end in cfg['painel']['enderecos']:
        try:
            servidores.append(ThreadingHTTPServer((end, porta), H))
        except OSError as e:
            print(f'painel: {end}:{porta} indisponível ({e})', file=sys.stderr)
    if not servidores:
        return 1
    for s in servidores[1:]:
        threading.Thread(target=s.serve_forever, daemon=True).start()
    print('painel em ' + ', '.join(f'http://{s.server_address[0]}:{porta}/' for s in servidores), flush=True)
    servidores[0].serve_forever()
    return 0
