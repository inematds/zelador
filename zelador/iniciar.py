"""Diagnóstico e instalação: vê o que a pessoa já tem, propõe o que falta e só escreve com --aplicar.

Para cada peça há três saídas:
  JÁ TEM      — o zelador usa como está;
  PROPOSTA    — existe algo parecido com outro nome ou formato: propõe mapear na config, nunca cria um gêmeo;
  CRIAR       — não existe nada: cria a partir do modelo (só com --aplicar, nunca sobrescreve).
"""
import getpass
import re
import shutil
import subprocess
from pathlib import Path

from . import config, controle

MODELOS = Path(__file__).with_name('modelos')
TIPOS = {
    'falhas': ('FALHAS.md', 'uma linha por falha: data, o que quebrou, menor correção, prompt/infra'),
    'licoes': ('LESSONS.md', 'o que aprendeu e não quer esquecer'),
    'limites': ('LIMITES.md', 'o que uma ferramenta, permissão ou cota te impediu de fazer'),
    'pendencias': ('PENDENCIAS.md', 'o que ficou para depois'),
}
MONITOR = re.compile(r'vigia|monit|watchdog|jardineiro|loopr|health|alerta?s?$', re.I)
INSTRUCOES = ['~/.claude/CLAUDE.md', '~/AGENTS.md', '~/.codex/AGENTS.md']


def sh(cmd):
    if not shutil.which(cmd[0]):
        return ''
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return ''


def diagnosticar(cfg):
    """Lista de achados: {peca, estado: tem|proposta|criar|info, texto, acao?}."""
    A = []

    def add(peca, estado, texto, acao=None):
        A.append({'peca': peca, 'estado': estado, 'texto': texto, 'acao': acao})

    if cfg['_existe']:
        add('config', 'tem', f"configuração em {cfg['_arquivo']}")
    else:
        add('config', 'criar', f"configuração nova em {cfg['_arquivo']} com o que foi detectado abaixo",
            {'tipo': 'config'})
    rz = [r for r in config.raizes(cfg) if r.is_dir()]
    if not rz:
        add('raizes', 'proposta', f"nenhuma pasta de projetos encontrada em {cfg['geral']['raizes']}: "
                                  'diga onde ficam com `--raiz <pasta>`')
        return A
    projs = [p for p in controle.projetos(cfg) if (p / '.git').exists()]
    add('raizes', 'info', f"{', '.join(map(str, rz))} · {len(projs)} projeto(s) com git")

    for tipo, (nome, para) in TIPOS.items():
        achados = controle.achar(cfg, tipo)
        parecidos = controle.parecidos(cfg, tipo)
        if achados:
            add(tipo, 'tem', f'{len(achados)} arquivo(s) de {tipo}: ' + ', '.join(
                f'{p.parent.name}/{p.name}' for p in achados[:6]) + (' …' if len(achados) > 6 else ''))
        for p in parecidos[:5]:
            if achados:  # já tem o padrão: o parecido é só sugestão, --aplicar não mexe
                add(tipo, 'proposta', f'`{p.parent.name}/{p.name}` parece {tipo} fora do padrão: se for, acrescente '
                                      f'"{p.name}" em arquivos.{tipo} (não aplicado sozinho)')
            else:  # o nome da pessoa é o sistema dela: mapear em vez de criar um gêmeo
                add(tipo, 'proposta', f'você já usa `{p.parent.name}/{p.name}` com cara de {tipo}: mapear na config '
                                      f'(arquivos.{tipo}) em vez de criar outro',
                    {'tipo': 'mapear', 'chave': tipo, 'valor': p.name})
        if not achados and not parecidos:
            destino = config.hub(cfg) / nome
            add(tipo, 'criar', f'nenhum arquivo de {tipo} ({para}): criar `{destino}` a partir do modelo',
                {'tipo': 'arquivo', 'modelo': nome, 'destino': str(destino)})
    if projs:
        sem = [p for p in projs if not any((p / n).exists() for n in cfg['arquivos']['falhas'])]
        if sem and len(sem) < len(projs):
            add('falhas', 'info', f'{len(sem)} de {len(projs)} projeto(s) sem arquivo de falhas próprio '
                                  f"(ex.: {', '.join(p.name for p in sem[:5])}). Opcional: o hub já cobre; "
                                  'crie por projeto quando ele tiver falhas próprias.')

    # instruções para o agente: sem elas, os arquivos ficam vazios
    blocos = [Path(i).expanduser() for i in INSTRUCOES if Path(i).expanduser().is_file()]
    fala = [b for b in blocos if re.search(r'FALHAS\.md|LIMITES\.md', b.read_text(errors='replace'))]
    if fala:
        add('instrucoes', 'tem', 'o agente já é instruído a registrar falhas/limites: ' + ', '.join(map(str, fala)))
    else:
        alvo = blocos[0] if blocos else Path(INSTRUCOES[0]).expanduser()
        add('instrucoes', 'proposta', f'nenhuma instrução manda o agente registrar falhas: colar o bloco de '
                                      f'`zelador bloco` em {alvo} (o zelador não edita esse arquivo sozinho)')

    # fontes da madrugada
    tem_j = bool(sh(['journalctl', '--user', '-n', '1', '--no-pager']).strip())
    add('journal', 'tem' if tem_j else 'info', 'journal do usuário legível (falhas de serviço, OOM, erros)'
        if tem_j else 'sem journal do usuário: a madrugada pula essa fonte')
    cron = sh(['crontab', '-l'])
    logs = re.findall(r'>>?\s*(\S+\.log)', cron)
    add('cron', 'tem' if logs else 'info', f'{len(logs)} log(s) de cron para vigiar' if logs
        else 'nenhum log de cron com `>> arquivo.log`: a madrugada pula essa fonte')

    # monitores que a pessoa já tem
    timers = sh(['systemctl', '--user', 'list-timers', '--all', '--no-pager', '--plain', '--no-legend'])
    nomes = sorted({l.split()[-1].removesuffix('.service') for l in timers.splitlines()
                    if l.split() and MONITOR.search(l.split()[-1]) and 'zelador' not in l})
    if nomes:
        add('monitores', 'proposta', 'você já tem monitores: ' + ', '.join(nomes) + '. Se algum grava relatório '
                                     '.md com listas, ligue como fonte em `pauta.relatorios` em vez de duplicar')
    aqa = [p for p in projs if (p / 'aprende' / 'comum.py').is_file()]
    if aqa and cfg['pauta']['recorrencia'] == 'interna':
        add('recorrencia', 'proposta', f'achei o agente-que-aprende em {aqa[0]}: usar o motor dele para as falhas '
                                       'que voltam (mais preciso)', {'tipo': 'set', 'secao': 'pauta',
                                                                     'chave': 'recorrencia', 'valor': str(aqa[0])})

    # aviso, explicação, agendamento
    if cfg['aviso']['comando']:
        add('aviso', 'tem', f"aviso por: {' '.join(cfg['aviso']['comando'])}")
    else:
        add('aviso', 'proposta', 'sem aviso: o relatório só fica em arquivo. Opções: `aviso.comando = '
                                 '["notify-send", "zelador"]` (desktop) ou o script do seu bot (Telegram) — '
                                 'modelo em modelos/avisar-telegram.sh')
    if not cfg['explicar']['comando']:
        add('explicar', 'info', 'explicação por IA desligada: cada item mostra o resumo fixo. Para ligar, '
                                '`explicar.comando` com um comando que lê o pedido no stdin (ex.: ["claude", "-p"])')
    usuario = getpass.getuser()
    linger = sh(['loginctl', 'show-user', usuario, '-p', 'Linger']).strip()
    if linger == 'Linger=no':
        add('agenda', 'proposta', 'sem ninguém conectado, os agendamentos deste usuário não rodam: em servidor, ative com '
                                  f'`sudo loginctl enable-linger {usuario}` (o zelador não faz isso sozinho)')
    sem_log = [l for l in cron.splitlines() if re.match(r'\s*(@\w+|[\d*/,-]+(\s+[\w*/,-]+){4})\s', l)
               and not re.search(r'>>?\s*\S+\.log', l)]
    if sem_log:
        add('cron', 'proposta', f'{len(sem_log)} tarefa(s) do cron sem arquivo de registro: a madrugada não vê se elas '
                                'falharam. Acrescente `>> arquivo.log 2>&1` a cada uma')
    add('alcance', 'info', 'a ronda vê as rotinas desta conta de usuário; rotinas do sistema, do administrador ou de '
                           'outra conta ficam de fora')
    ag = sh(['systemctl', '--user', 'list-unit-files', '--no-pager', '--plain', '--no-legend', 'zelador-*'])
    if 'zelador-noite.timer' in ag:
        add('agenda', 'tem', 'timers do zelador instalados')
    else:
        add('agenda', 'proposta', 'agendar madrugada (04:20), pauta (segunda 07:45) e painel: `zelador agendar --aplicar`')
    return A


def aplicar(cfg, achados, raiz=None):
    """Executa as ações CRIAR e as propostas de mapear/config; nunca sobrescreve arquivo existente."""
    feitos = []
    novo = {k: dict(v) for k, v in cfg.items() if not k.startswith('_')}
    if raiz:
        novo['geral']['raizes'] = [raiz]
    for a in achados:
        ac = a.get('acao') or {}
        if ac.get('tipo') == 'arquivo':
            d = Path(ac['destino'])
            if not d.exists():
                d.parent.mkdir(parents=True, exist_ok=True)
                d.write_text((MODELOS / ac['modelo']).read_text())
                feitos.append(f'criado {d}')
        elif ac.get('tipo') == 'mapear':
            lst = novo['arquivos'][ac['chave']]
            if ac['valor'] not in lst:
                novo['arquivos'][ac['chave']] = [*lst, ac['valor']]
                feitos.append(f"mapeado {ac['valor']} como {ac['chave']}")
        elif ac.get('tipo') == 'set':
            novo[ac['secao']][ac['chave']] = ac['valor']
            feitos.append(f"{ac['secao']}.{ac['chave']} = {ac['valor']}")
    p = Path(cfg['_arquivo'])
    if not p.exists() or any('mapeado' in f or ' = ' in f for f in feitos):
        if p.exists():
            shutil.copy2(p, p.with_suffix('.toml.antes'))
            feitos.append(f'cópia da config anterior em {p.with_suffix(".toml.antes")}')
        config.escrever(novo, p)
        feitos.append(f'config gravada em {p}')
    return feitos


def texto(achados):
    rot = {'tem': '✓ JÁ TEM', 'proposta': '→ PROPOSTA', 'criar': '+ CRIAR', 'info': '· info'}
    return '\n'.join(f"{rot[a['estado']]:<12} [{a['peca']}] {a['texto']}" for a in achados)
