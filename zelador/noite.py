"""Vigia da madrugada: o que foi grave ou repetido nas últimas horas. Sem LLM.

GRAVE: rotina com timer que falhou, morte por falta de memória, disco no limite, mesmo erro N+ vezes.
ATENÇÃO: serviço avulso que falhou, erro repetido menor, erros novos nos logs do cron,
         linhas novas nos FALHAS/LIMITES, unidades presas em 'failed'.
Cada fonte só roda se existir na máquina (journalctl, crontab, systemctl); a que falta é pulada.
"""
import collections
import datetime as dt
import json
import re
import shutil
import subprocess
from pathlib import Path

from . import avisar, config, controle

ERRO_LOG = re.compile(r'Traceback \(most recent|\bERROR\b|\bFATAL\b|\bfatal:|Killed|MemoryError|No space left', re.I)


def sh(cmd, timeout=120):
    if not shutil.which(cmd[0]):
        return ''
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ''


def normaliza(msg):
    m = re.sub(r'0x[0-9a-f]+|\b[0-9a-f]{8,}\b', 'H', msg, flags=re.I)
    m = re.sub(r'\d+', '#', m)
    m = re.sub(r'/tmp/\S+', '/tmp/…', m)
    return re.sub(r'\s+', ' ', m).strip()[:160]


def rotinas():
    saida = sh(['systemctl', '--user', 'list-timers', '--all', '--no-pager', '--plain', '--no-legend'])
    return {l.split()[-1] for l in saida.splitlines() if l.split() and l.split()[-1].endswith('.service')}


def journal(horas, ignorar):
    falhas, erros, exemplo, oom = collections.Counter(), collections.Counter(), {}, []
    if not shutil.which('journalctl'):
        return falhas, erros, exemplo, oom, False
    proc = subprocess.Popen(['journalctl', '--user', '--since', f'-{horas}h', '-o', 'json', '--no-pager'],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, errors='replace')
    for linha in proc.stdout:
        try:
            e = json.loads(linha)
        except ValueError:
            continue
        msg = e.get('MESSAGE')
        if not isinstance(msg, str):
            continue
        unidade = e.get('USER_UNIT') or e.get('_SYSTEMD_USER_UNIT') or e.get('SYSLOG_IDENTIFIER') or '?'
        if 'Failed with result' in msg and e.get('USER_UNIT'):
            falhas[e['USER_UNIT']] += 1
            continue
        if 'killed by the OOM killer' in msg and e.get('USER_UNIT', '').endswith(('.service', '.scope')):
            oom.append(e['USER_UNIT'])
        if unidade in ignorar:
            continue
        if int(e.get('PRIORITY', 6)) <= 3:
            chave = (unidade, normaliza(msg))
            erros[chave] += 1
            exemplo.setdefault(chave, msg[:200])
    proc.wait()
    return falhas, erros, exemplo, oom, True


def oom_kernel(horas):
    return re.findall(r'Killed process \d+ \(([^)]+)\)',
                      sh(['journalctl', '-k', '--since', f'-{horas}h', '--no-pager', '-o', 'cat']))


def logs_cron(estado):
    vistos, achados = estado.setdefault('cron', {}), []
    for l in sh(['crontab', '-l']).splitlines():
        if l.lstrip().startswith('#'):
            continue
        for alvo in re.findall(r'>>?\s*(\S+\.log)', l):
            p = Path(alvo).expanduser()
            if not p.is_file():
                continue
            tam = p.stat().st_size
            ini = vistos.get(alvo, max(0, tam - 200_000))
            if ini > tam:
                ini = 0
            with p.open('rb') as f:
                f.seek(ini)
                novo = f.read(2_000_000).decode('utf-8', 'replace')
            vistos[alvo] = tam
            linhas = [x for x in novo.splitlines() if ERRO_LOG.search(x)]
            if linhas:
                achados.append((alvo, len(linhas), linhas[-1][:160]))
    return achados


def registros_novos(cfg, estado):
    contagem, novos = estado.setdefault('registros', {}), []
    for p in controle.achar(cfg, 'falhas') + controle.achar(cfg, 'limites'):
        n = len(controle.registros(p))
        antes = contagem.get(str(p))
        contagem[str(p)] = n
        if antes is not None and n > antes:
            novos.append((p, n - antes))
    return novos


def presos():
    saida = sh(['systemctl', '--user', '--failed', '--no-pager', '--plain', '--no-legend'])
    return [l.split()[0] for l in saida.splitlines() if l.split()]


def rodar(cfg, horas=None, sem_aviso=False):
    c = cfg['noite']
    horas = horas or c['horas']
    pasta = config.dados(cfg, 'noite')
    arq_estado = config.dados(cfg) / 'estado-noite.json'
    estado = json.loads(arq_estado.read_text()) if arq_estado.is_file() else {}
    hoje = dt.date.today().isoformat()
    fontes, puladas = [], []

    falhas, erros, exemplo, oom, tem_journal = (journal(horas, set(c['ignorar'])) if c['journal']
                                                else (collections.Counter(), collections.Counter(), {}, [], False))
    (fontes if tem_journal else puladas).append('journal')
    mortos = oom_kernel(horas) if tem_journal else []
    ts = rotinas()
    cron = []
    if c['cron'] and shutil.which('crontab'):
        cron = logs_cron(estado)
        fontes.append('cron')
    else:
        puladas.append('cron')
    novos = registros_novos(cfg, estado)
    presos_lista = presos()
    disco = shutil.disk_usage('/')
    disco_pct = round(100 * disco.used / disco.total)

    grave, atencao = [], []
    for u, n in falhas.most_common():
        if u in oom:
            continue
        (grave if u in ts else atencao).append(f"{'rotina' if u in ts else 'avulso'} `{u}` falhou {n}×")
    if oom or mortos:
        nomes = ', '.join(f'{k} {v}×' for k, v in collections.Counter(mortos).most_common(5)) or '?'
        servicos = [u for u in dict.fromkeys(oom) if u.endswith('.service')]
        grave.append(f'falta de memória: {max(len(mortos), len(oom))} processo(s) mortos pelo OOM ({nomes})'
                     + (f" — serviços: {', '.join(servicos[:5])}" if servicos
                        else f' — em {len(set(oom))} trecho(s) avulso(s)'))
    if disco_pct >= c['disco_grave']:
        grave.append(f'disco / em {disco_pct}%')
    elif disco_pct >= c['disco_atencao']:
        atencao.append(f'disco / em {disco_pct}%')
    for (u, m), n in erros.most_common():
        if n >= c['repetido_grave']:
            grave.append(f'erro repetido {n}× em `{u}`: {exemplo[(u, m)][:120]}')
        elif n >= c['repetido_atencao']:
            atencao.append(f'erro repetido {n}× em `{u}`: {exemplo[(u, m)][:120]}')
    for alvo, n, ult in cron:
        atencao.append(f'cron `{Path(alvo).name}`: {n} linha(s) de erro — última: {ult[:110]}')
    for p, n in novos:
        atencao.append(f'{n} registro(s) novo(s) em {p.parent.name}/{p.name}')
    velhos = [u for u in presos_lista if u not in falhas]
    if velhos:
        atencao.append(f"{len(velhos)} unidade(s) presa(s) em 'failed' de antes: " + ', '.join(velhos[:8])
                       + (' …' if len(velhos) > 8 else ''))

    L = [f'# Zelador — madrugada {hoje} (últimas {horas} h)', '',
         f'- grave: {len(grave)} · atenção: {len(atencao)} · disco {disco_pct}% · '
         f'{sum(erros.values())} erro(s) no journal em {len(erros)} tipo(s)',
         f"- fontes lidas: {', '.join(fontes) or 'nenhuma'}" + (f" · puladas (não existem aqui): {', '.join(puladas)}" if puladas else ''),
         '', '## Grave', ''] + ([f'- {x}' for x in grave] or ['- nada']) + \
        ['', '## Atenção', ''] + ([f'- {x}' for x in atencao] or ['- nada']) + \
        ['', '## Erros mais frequentes no journal', '']
    L += [f'- {n}× `{u}` — {exemplo[(u, m)][:150]}' for (u, m), n in erros.most_common(15)] or ['- nenhum']
    L += ['', 'Como agir: `journalctl --user -u <unidade> -n 50`; depois de corrigir, uma linha no FALHAS.md.',
          "Unidade avulsa velha em 'failed' que não importa mais: `systemctl --user reset-failed <unidade>`."]
    rel = pasta / f'{hoje}.md'
    rel.write_text('\n'.join(L) + '\n')
    (pasta / f'{hoje}.json').write_text(json.dumps({'grave': grave, 'atencao': atencao}, ensure_ascii=False, indent=1))
    estado['ultima'] = hoje
    arq_estado.write_text(json.dumps(estado, ensure_ascii=False, indent=1))
    resultado = {'relatorio': str(rel), 'grave': len(grave), 'atencao': len(atencao)}
    if sem_aviso:
        return resultado
    if grave:
        msg = f'🌙 Madrugada {hoje}: {len(grave)} GRAVE, {len(atencao)} atenção\n' + \
              '\n'.join(f'• {x}' for x in grave[:8]) + f'\nRelatório: {rel}'
    elif atencao:
        msg = f'🌙 Madrugada {hoje}: nada grave, {len(atencao)} ponto(s) de atenção\n' + \
              '\n'.join(f'• {x}' for x in atencao[:5]) + f'\nRelatório: {rel}'
    elif c['avisar_limpa']:
        msg = f'🌙 Madrugada {hoje}: limpa, nenhum erro grave ou repetido.'
    else:
        return resultado
    resultado['aviso'] = avisar.avisar(cfg, msg)
    return resultado
