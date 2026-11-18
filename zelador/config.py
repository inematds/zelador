"""Configuração do zelador: um TOML na casa da pessoa, com padrões que funcionam sem nada configurado."""
import copy
import os
import tomllib
from pathlib import Path

VERSAO = '1.0.2'

PADRAO = {
    'geral': {
        'raizes': ['~/projetos'],          # onde procurar projetos e arquivos de controle
        'hub': '',                         # pasta dos arquivos gerais (PENDENCIAS/LIMITES); vazio = 1ª raiz
        'dados': '~/.local/share/zelador', # relatórios, pautas, decisões (fora do código)
    },
    'arquivos': {                          # nomes que contam como cada tipo de controle
        'falhas': ['FALHAS.md'],
        'licoes': ['LESSONS.md', 'LICOES.md'],
        'limites': ['LIMITES.md'],
        'pendencias': ['PENDENCIAS.md', 'pendencias.md'],
    },
    'aviso': {
        'comando': [],                     # a mensagem entra como último argumento; vazio = só grava o relatório
    },
    'noite': {
        'horas': 24,
        'repetido_grave': 20,
        'repetido_atencao': 5,
        'disco_atencao': 85,
        'disco_grave': 90,
        'journal': True,
        'cron': True,
        'ignorar': [],                     # unidades/identificadores que são só barulho
        'avisar_limpa': True,              # manda uma linha mesmo quando a noite foi limpa
        'trechos': True,                   # false = aviso e relatório sem trechos dos registros (dados sensíveis)
    },
    'pauta': {
        'top': 12,
        'pendencia_parada_dias': 14,
        'recusa_semanas': 8,
        'limites_max': 8,
        'pendencias_max': 8,
        'recorrencia': 'interna',          # 'interna' ou o caminho do agente-que-aprende
        'grupos': [],                      # [{nome, glob}] — FALHAS novos da semana de um grupo de projetos
        'relatorios': [],                  # [{nome, pasta}] — último .md de outro monitor; listas viram itens
    },
    'explicar': {
        'comando': [],                     # recebe o pedido no stdin e devolve texto (ou JSON com "texto")
        'cwd': '',
        'max_chamadas': 3,
        'timeout': 420,
    },
    'painel': {
        'enderecos': ['127.0.0.1'],
        'porta': 8810,
        'link': '',                        # endereço que vai no aviso; vazio = http://127.0.0.1:<porta>/
    },
}


def caminho_config():
    return Path(os.environ.get('ZELADOR_CONFIG', '~/.config/zelador/zelador.toml')).expanduser()


def mesclar(base, extra):
    out = copy.deepcopy(base)
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = mesclar(out[k], v)
        else:
            out[k] = v
    return out


def carregar(caminho=None):
    p = Path(caminho).expanduser() if caminho else caminho_config()
    dados = tomllib.loads(p.read_text()) if p.is_file() else {}
    cfg = mesclar(PADRAO, dados)
    cfg['_arquivo'] = str(p)
    cfg['_existe'] = p.is_file()
    return cfg


def raizes(cfg):
    return [Path(r).expanduser() for r in cfg['geral']['raizes']]


def hub(cfg):
    h = cfg['geral'].get('hub')
    return Path(h).expanduser() if h else raizes(cfg)[0]


def dados(cfg, *sub):
    p = Path(cfg['geral']['dados']).expanduser().joinpath(*sub)
    p.mkdir(parents=True, exist_ok=True)
    return p


def link_painel(cfg):
    return cfg['painel']['link'] or f"http://127.0.0.1:{cfg['painel']['porta']}/"


def toml_valor(v):
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(v, list):
        return '[' + ', '.join(toml_valor(x) for x in v) + ']'
    if isinstance(v, dict):
        return '{' + ', '.join(f'{k} = {toml_valor(x)}' for k, x in v.items()) + '}'
    raise TypeError(v)


def escrever(cfg, caminho, comentarios=None):
    """Grava só as seções/chaves conhecidas, com um comentário por seção."""
    comentarios = comentarios or {}
    linhas = [f'# zelador {VERSAO} — gerado por `zelador iniciar --aplicar`. Edite à vontade.', '']
    for secao, chaves in PADRAO.items():
        if comentarios.get(secao):
            linhas.append(f'# {comentarios[secao]}')
        linhas.append(f'[{secao}]')
        for k in chaves:
            linhas.append(f'{k} = {toml_valor(cfg[secao][k])}')
        linhas.append('')
    p = Path(caminho).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('\n'.join(linhas))
    return p
