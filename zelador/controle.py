"""Achar e ler os arquivos de controle (falhas, lições, limites, pendências) nas raízes configuradas."""
import datetime as dt
import re
from pathlib import Path

from . import config

# Nomes parecidos que a pessoa pode já usar: o zelador propõe mapear, nunca cria um gêmeo.
PARECIDOS = {
    'falhas': re.compile(r'^(erros?|errors?|bugs?|falhas?|incidentes?|incidents?|failures?|postmortems?|problemas?)'
                         r'([-_ ].*)?\.(md|txt)$', re.I),
    'licoes': re.compile(r'^(lessons?|li[cç](oe|õe)s|aprendizados?|learnings?|retro(spectiva)?s?)([-_ ].*)?\.(md|txt)$', re.I),
    'limites': re.compile(r'^(limites?|limits?|bloqueios?|blockers?|impedimentos?)([-_ ].*)?\.(md|txt)$', re.I),
    'pendencias': re.compile(r'^(todo|to-do|pend[eê]ncias?|backlog|tarefas?|tasks?)([-_ ].*)?\.(md|txt)$', re.I),
}


def projetos(cfg):
    """Pastas de projeto: a própria raiz e as subpastas imediatas."""
    out = []
    for r in config.raizes(cfg):
        if not r.is_dir():
            continue
        out.append(r)
        out += sorted(p for p in r.iterdir() if p.is_dir() and not p.name.startswith('.'))
    return out


def nomes(cfg, tipo):
    return [n for n in cfg['arquivos'][tipo] if '/' not in n and not n.startswith('~')]


def caminhos_fixos(cfg, tipo):
    return [Path(n).expanduser() for n in cfg['arquivos'][tipo] if '/' in n or n.startswith('~')]


def achar(cfg, tipo):
    """Arquivos reconhecidos de um tipo (por nome em cada projeto + caminhos fixos da config)."""
    vistos, out = set(), []
    for p in caminhos_fixos(cfg, tipo):
        if p.is_file() and p.resolve() not in vistos:
            vistos.add(p.resolve())
            out.append(p)
    for proj in projetos(cfg):
        for n in nomes(cfg, tipo):
            p = proj / n
            if p.is_file() and p.resolve() not in vistos:
                vistos.add(p.resolve())
                out.append(p)
    return out


def parecidos(cfg, tipo):
    """Arquivos com cara de controle que não estão na config (candidatos a mapear)."""
    conhecidos = {p.resolve() for t in PARECIDOS for p in achar(cfg, t)}
    aceitos = {n.lower() for t in PARECIDOS for n in cfg['arquivos'][t]}
    out = []
    for proj in projetos(cfg):
        try:
            itens = list(proj.iterdir())
        except OSError:
            continue
        for p in itens:
            if (p.is_file() and PARECIDOS[tipo].match(p.name) and p.resolve() not in conhecidos
                    and p.name.lower() not in aceitos and p.name.lower() not in ('readme.md', 'changelog.md')):
                out.append(p)
    return out


def data_de(txt):
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', txt)
    if m:
        try:
            return dt.date(*map(int, m.groups()))
        except ValueError:
            return None
    m = re.search(r'(\d{2})/(\d{2})/(\d{4})', txt)
    if m:
        d, mes, a = map(int, m.groups())
        try:
            return dt.date(a, mes, d)
        except ValueError:
            return None
    return None


def registros(caminho):
    """Linhas de tabela `| data | o que quebrou | correção | ... |` ou itens `- texto (data)`."""
    p = Path(caminho)
    out = []
    for n, linha in enumerate(p.read_text(errors='replace').splitlines(), 1):
        s = linha.strip()
        if s.startswith('|'):
            cel = [c.strip() for c in s.strip('|').split('|')]
            if len(cel) < 3 or not re.match(r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}', cel[0]):
                continue
            out.append({'arquivo': str(p), 'linha': n, 'data': cel[0], 'problema': cel[1],
                        'correcao': cel[2], 'celulas': cel, 'texto': ' '.join(cel[1:3])})
        elif s.startswith('- ') and len(s) > 25 and not s.startswith('- [x]'):
            txt = s[2:]
            out.append({'arquivo': str(p), 'linha': n, 'data': (data_de(txt) or '') and str(data_de(txt)),
                        'problema': txt, 'correcao': txt, 'celulas': [], 'texto': txt})
    return out
