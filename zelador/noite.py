"""Vigia da madrugada: o que foi grave ou repetido nas últimas horas. Sem LLM.

GRAVE: rotina com timer que falhou ou parou de rodar (ele aprende o ritmo de cada uma), falta de memória,
       disco no limite, mesmo erro N+ vezes.
ATENÇÃO: serviço avulso que falhou, rotina que terminou mas escreveu erro, erro repetido menor, erros novos
         nos logs do cron, tarefa do cron sem atividade, linhas novas nos FALHAS/LIMITES, unidades em 'failed'.
Cada fonte só roda se existir na máquina (journalctl, crontab, systemctl); a que falta é pulada.
"""
import collections
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from . import avisar, config, controle

ERRO_LOG = re.compile(r'Traceback \(most recent|\bERROR\b|\bFATAL\b|\bfatal:|Killed|MemoryError|No space left'
                      r'|\berro\b|\bfalhou\b|\bfalha\b|(?<!\b0 )\bfailed\b|\bexception\b'
                      r'|permission denied|permissão negada|no such file|command not found|cannot |não foi possível', re.I)

PRIORITARIOS = ('a rotina', 'tarefa agendada')
NEGADO = re.compile(r'\b(sem|nenhum|nenhuma|0|zero|no|without)\s+(erros?|falhas?|errors?|failures?)\b', re.I)


def tem_erro(linha):
    return bool(ERRO_LOG.search(NEGADO.sub(' ', linha)))


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
    falhas, erros, exemplo, oom, saida = collections.Counter(), collections.Counter(), {}, [], {}
    if not shutil.which('journalctl'):
        return falhas, erros, exemplo, oom, False, saida
    proc = subprocess.Popen(['journalctl', '--user', '--since', f'-{horas}h', '-o', 'json', '--no-pager'],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, errors='replace')
    leu = False
    for linha in proc.stdout:
        leu = True
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
        elif str(e.get('_SYSTEMD_USER_UNIT', '')).endswith('.service') and tem_erro(msg):
            # a rotina pode terminar "com sucesso" tendo escrito erro na própria saída
            n, _ = saida.get(e['_SYSTEMD_USER_UNIT'], (0, ''))
            saida[e['_SYSTEMD_USER_UNIT']] = (n + 1, msg[:160])
    proc.wait()
    return falhas, erros, exemplo, oom, leu, saida  # sem nenhuma linha, não dá para dizer que a noite foi limpa


def oom_kernel(horas):
    """Programas encerrados por falta de memória; None se não deu para ler os registros do sistema."""
    try:
        r = subprocess.run(['journalctl', '-k', '--since', f'-{horas}h', '--no-pager', '-o', 'cat'],
                           capture_output=True, text=True, timeout=120)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    return re.findall(r'Killed process \d+ \(([^)]+)\)', r.stdout)


def ler_novo(p, vistos):
    """Linhas com erro acrescentadas ao arquivo desde a última leitura: (linhas, primeira_leitura)."""
    alvo, tam = str(p), p.stat().st_size
    primeira = alvo not in vistos
    ini = vistos.get(alvo, max(0, tam - 200_000))
    if ini > tam:
        ini = 0
    with p.open('rb') as f:
        f.seek(ini)
        novo = f.read(2_000_000).decode('utf-8', 'replace')
    vistos[alvo] = tam
    return [x for x in novo.splitlines() if tem_erro(x)], primeira


def tempo(seg):
    return f'{round(seg / 86400)} dia(s)' if seg >= 129600 else f'{max(1, round(seg / 3600))} hora(s)'


def periodo_cron(linha):
    """De quanto em quanto tempo a tarefa deveria rodar, no mínimo (segundos); None se não dá para saber."""
    c = linha.split()
    if c[0].startswith('@'):
        return {'@hourly': 3600, '@daily': 86400, '@midnight': 86400, '@weekly': 604800, '@monthly': 2678400}.get(c[0])
    if c[4] != '*':
        return 604800
    return 2678400 if c[2] != '*' or c[3] != '*' else 86400


def inicios_rotinas(dias=35):
    """Quando cada serviço começou a rodar, pelo histórico que a própria máquina guarda."""
    out = collections.defaultdict(list)
    if not shutil.which('journalctl'):
        return out
    proc = subprocess.Popen(['journalctl', '--user', '--since', f'-{dias}d', '-t', 'systemd', '-o', 'json',
                             '--output-fields=MESSAGE,USER_UNIT', '--no-pager'],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, errors='replace')
    for linha in proc.stdout:
        if '"Starting ' not in linha:
            continue
        try:
            e = json.loads(linha)
            if e.get('USER_UNIT'):
                out[e['USER_UNIT']].append(int(e['__REALTIME_TIMESTAMP']) / 1e6)
        except (ValueError, KeyError, TypeError):
            continue
    proc.wait()
    return out


def rotinas_paradas(estado, agora=None, inicios=None):
    """Aponta o timer ativo que passou do maior intervalo normal dele. O ritmo vem do histórico da máquina."""
    agora = agora or time.time()
    try:
        timers = json.loads(sh(['systemctl', '--user', 'list-timers', '--all', '--output=json', '--no-pager']) or '[]')
    except ValueError:
        return []
    ativos = {l.split()[0] for l in sh(['systemctl', '--user', 'list-unit-files', '--type=timer', '--state=enabled',
                                        '--no-legend', '--no-pager']).splitlines() if l.split()}
    if not timers or not ativos:
        return []
    inicios = inicios_rotinas() if inicios is None else inicios
    hist, out = estado.setdefault('timers', {}), []
    for t in timers:
        u, ultimo = t.get('unit'), (t.get('last') or 0) / 1e6
        if u not in ativos or not ultimo:
            continue
        h = hist.setdefault(u, [])  # reserva para máquina que guarda pouco histórico
        if not h or ultimo > h[-1] + 1:
            h.append(int(ultimo))
            del h[:-9]
        vistos = []
        for x in sorted(inicios.get(t.get('activates'), [])):
            if not vistos or x - vistos[-1] > 60:
                vistos.append(x)
        base = vistos[-9:] if len(vistos) >= 3 else h
        if len(base) < 3:
            continue
        vaos = [b - a for a, b in zip(base, base[1:])]
        if agora - ultimo > max(vaos) + 3600:
            out.append((u.removesuffix('.timer'), agora - ultimo, sorted(vaos)[len(vaos) // 2]))
    return out


def logs_das_rotinas(estado, ts):
    """Rotinas que gravam a saída num arquivo próprio (StandardOutput=append:...): erros novos nele."""
    achados, vistos = {}, estado.setdefault('cron', {})
    if not ts:
        return achados
    unidade = None
    for l in sh(['systemctl', '--user', 'cat', '--no-pager', *sorted(ts)]).splitlines():
        if l.startswith('# /'):
            unidade = Path(l[2:].strip()).name
        m = re.match(r'Standard(?:Output|Error)=(?:append|file):(\S+)', l)
        if m and unidade in ts:
            p = Path(m.group(1).replace('%h', str(Path.home()))).expanduser()
            if p.is_absolute() and p.is_file():
                linhas, _ = ler_novo(p, vistos)
                if linhas:
                    n, _ = achados.get(unidade, (0, ''))
                    achados[unidade] = (n + len(linhas), linhas[-1][:160])
    return achados


def logs_cron(estado):
    """Erros novos nos logs do cron. Devolve (achados, tarefas, tarefas_sem_log, paradas)."""
    vistos, achados, paradas = estado.setdefault('cron', {}), [], []
    tarefas = sem_log = 0
    agora = time.time()
    for l in sh(['crontab', '-l']).splitlines():
        if l.lstrip().startswith('#') or not re.match(r'\s*(@\w+|[\d*/,-]+(\s+[\w*/,-]+){4})\s', l):
            continue
        tarefas += 1
        cd = re.search(r'\bcd\s+([^\s;&]+)', l)  # log relativo: vale a pasta do `cd` da própria linha
        base = Path(os.path.expandvars(cd.group(1))).expanduser() if cd else Path()
        alvos = [base / Path(os.path.expandvars(a)).expanduser() for a in re.findall(r'>>?\s*(\S+\.log)', l)]
        alvos = [p for p in alvos if p.is_absolute() and p.is_file()]
        sem_log += not alvos  # sem arquivo legível, esta tarefa não foi olhada
        periodo = periodo_cron(l)
        for p in alvos:
            linhas, primeira = ler_novo(p, vistos)
            if linhas:
                achados.append((str(p), len(linhas), linhas[-1][:160], primeira))
            parado = agora - p.stat().st_mtime
            if periodo and p.stat().st_size and parado > 2 * periodo + 21600:
                paradas.append((p.name, parado, periodo))
    return achados, tarefas, sem_log, paradas


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

    falhas, erros, exemplo, oom, tem_journal, saida = (journal(horas, set(c['ignorar'])) if c['journal']
                                                else (collections.Counter(), collections.Counter(), {}, [], False, {}))
    (fontes if tem_journal else puladas).append('journal')
    mortos = oom_kernel(horas) if tem_journal else []
    if mortos is None:
        mortos = []
        puladas.append('memoria')
    ts = rotinas()
    paradas = rotinas_paradas(estado)
    for u, v in logs_das_rotinas(estado, ts).items():
        n, _ = saida.get(u, (0, ''))
        saida[u] = (n + v[0], v[1])
    cron, cron_sem_log, cron_paradas = [], 0, []
    if c['cron'] and shutil.which('crontab'):
        cron, tarefas, cron_sem_log, cron_paradas = logs_cron(estado)
        if tarefas and tarefas == cron_sem_log:
            puladas.append('cron')
        elif tarefas:
            fontes.append('cron')
    else:
        puladas.append('cron')
    novos = registros_novos(cfg, estado)
    presos_lista = presos()
    disco = shutil.disk_usage('/')
    disco_pct = round(100 * disco.used / disco.total)

    grave, atencao, origem = [], [], {}

    def marca(lista, texto, **fonte):
        lista.append(texto)
        origem[texto.split(' — ')[0]] = fonte

    for u, n in falhas.most_common():
        if u in oom:
            continue
        nome = u.removesuffix('.service')
        marca(grave if u in ts else atencao, f"{'a rotina' if u in ts else 'a tarefa avulsa'} {nome} falhou {n}×", unidade=u)
    for nome, atraso, ritmo in paradas:
        marca(grave, f'a rotina {nome} parou de rodar: a última vez foi há {tempo(atraso)}, '
                     f'e ela costuma rodar a cada {tempo(ritmo)}', unidade=f'{nome}.service')
    for u, (n, ult) in sorted(saida.items(), key=lambda x: -x[1][0]):
        if u in ts and u not in falhas and u.removesuffix('.service') not in c['ignorar']:
            fim = f' — última: {ult[:110]}' if c['trechos'] else ''
            marca(atencao, f"a rotina {u.removesuffix('.service')} terminou, mas escreveu {n} linha(s) com erro{fim}", unidade=u)
    if oom or mortos:
        nomes = ', '.join(f'{k} {v}×' for k, v in collections.Counter(mortos).most_common(5)) or '?'
        servicos = [u for u in dict.fromkeys(oom) if u.endswith('.service')]
        grave.append(f'falta de memória: o sistema encerrou {max(len(mortos), len(oom))} programa(s) ({nomes})'
                     + (f" — serviços: {', '.join(servicos[:5])}" if servicos
                        else f' — em {len(set(oom))} trecho(s) avulso(s)'))
    if disco_pct >= c['disco_grave']:
        grave.append(f'disco / em {disco_pct}%')
    elif disco_pct >= c['disco_atencao']:
        atencao.append(f'disco / em {disco_pct}%')
    for (u, m), n in erros.most_common():
        if n >= c['repetido_grave']:
            grave.append(f'erro repetido {n}× em `{u}`' + (f': {exemplo[(u, m)][:120]}' if c['trechos'] else ''))
        elif n >= c['repetido_atencao']:
            atencao.append(f'erro repetido {n}× em `{u}`' + (f': {exemplo[(u, m)][:120]}' if c['trechos'] else ''))
    for alvo, n, ult, primeira in cron:
        extra = ' (primeira leitura: pode incluir erros antigos)' if primeira else ''
        fim = f' — última: {ult[:110]}' if c['trechos'] else ''
        marca(atencao, f'tarefa agendada ({Path(alvo).name}): {n} linha(s) com erro{extra}{fim}', arquivo=alvo)
    for nome, parado, periodo in cron_paradas:
        atencao.append(f'tarefa agendada ({nome}): sem nenhuma atividade há {tempo(parado)}, '
                       f'e deveria rodar a cada {tempo(periodo)}; pode ter parado')
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
    L += [f'- {n}× `{u}`' + (f' — {exemplo[(u, m)][:150]}' if c['trechos'] else '')
          for (u, m), n in erros.most_common(15)] or ['- nenhum']
    L += ['', f'Formulário da semana: {config.link_painel(cfg)}']
    L += ['', 'Como agir: `journalctl --user -u <unidade> -n 50`; depois de corrigir, uma linha no FALHAS.md.',
          "Unidade avulsa velha em 'failed' que não importa mais: `systemctl --user reset-failed <unidade>`."]
    rel = pasta / f'{hoje}.md'
    rel.write_text('\n'.join(L) + '\n')
    (pasta / f'{hoje}.json').write_text(json.dumps({'grave': grave, 'atencao': atencao, 'origem': origem}, ensure_ascii=False, indent=1))
    estado['ultima'] = hoje
    arq_estado.write_text(json.dumps(estado, ensure_ascii=False, indent=1))
    resultado = {'relatorio': str(rel), 'grave': len(grave), 'atencao': len(atencao)}
    resultado['nao_verificado'] = puladas
    resultado['cron_sem_log'] = cron_sem_log
    if sem_aviso:
        return resultado
    nomes_fonte = {'journal': 'registros do sistema (rotinas e falta de memória)', 'cron': 'tarefas agendadas no cron',
                   'memoria': 'programas encerrados por falta de memória fora dos serviços'}
    faltou = [nomes_fonte[p] for p in puladas]
    if cron_sem_log and 'cron' not in puladas:
        faltou.append(f'{cron_sem_log} tarefa(s) do cron sem arquivo de registro')
    ressalva = ('\nNão consegui verificar: ' + '; '.join(faltou) + '.') if faltou else ''
    if grave:
        msg = f'🌙 Madrugada {hoje}: {len(grave)} GRAVE, {len(atencao)} atenção\n' + \
              '\n'.join(f'• {x}' for x in grave[:8]) + \
              ''.join(f'\n• {x}' for x in [a for a in atencao if a.startswith(PRIORITARIOS)][:3]) + \
              f'\nRelatório: {rel}' + ressalva
    elif atencao:
        msg = f'🌙 Madrugada {hoje}: nada grave, {len(atencao)} ponto(s) de atenção\n' + \
              '\n'.join(f'• {x}' for x in sorted(atencao, key=lambda a: not a.startswith(PRIORITARIOS))[:5]) + \
              f'\nRelatório: {rel}' + ressalva
    elif faltou:  # nunca dizer "limpa" sobre o que não foi olhado
        msg = f'🌙 Madrugada {hoje}: nada encontrado no que consegui olhar.' + ressalva
    elif c['avisar_limpa']:
        msg = f'🌙 Madrugada {hoje}: limpa, nenhum erro grave ou repetido.'
    else:
        return resultado
    if grave or atencao:
        msg += '\nPara entender ou consertar, cole este aviso na sua IA.'
    resultado['aviso'] = avisar.avisar(cfg, msg)
    return resultado
