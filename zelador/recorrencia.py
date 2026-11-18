"""Falhas que voltam: agrupa registros parecidos dos FALHAS/LIÇÕES e diz que tipo de proteção falta.

Se `pauta.recorrencia` aponta para o agente-que-aprende, usa o motor dele (degraus e sugestões);
senão usa o agrupamento interno abaixo, mais simples.
"""
import re
import sys
import unicodedata
from pathlib import Path

from . import controle

PARADAS = set('''para pela pelo pelos pelas com sem uma umas uns dos das nos nas que por mas mais menos como quando
onde porque isso esse essa este esta isto aqui entao tambem ainda sempre nunca depois antes cada todo toda todos
todas muito outro outra sobre entre desde seu sua seus suas nao sim foi era ser ter tem tinha vai vez vezes ficou
fica deve pode faz fazer feito usar usa usou the and for with without this that from into when then have has was
were are not but also only just'''.split())

# Em linguagem simples: onde a correção está hoje e o que cada proteção faria.
HOJE = {
    'texto': 'só anotada num arquivo — depende de alguém lembrar de ler',
    'checklist': 'numa lista de conferência que alguém precisa seguir',
    'teste': 'coberta por um teste automático',
    'sonda': 'coberta por uma medição automática',
    'gancho/validador': 'barrada por uma trava automática',
    'servidor/arquitetura': 'resolvida no próprio sistema',
}
PROPOSTA = {
    'teste': 'Criar um teste automático que repete a situação do erro. Se alguém (pessoa ou agente) quebrar de novo, '
             'o teste fica vermelho antes de publicar: o erro é pego na máquina, não pelo público.',
    'sonda': 'Criar uma medição automática que confere o resultado (tamanho, duração, limite) e acusa quando passa '
             'do teto, antes de seguir.',
    'gancho/validador': 'Criar uma trava automática: antes de executar o passo, um verificador olha o comando ou o '
                        'arquivo e barra se for o erro conhecido, mostrando a lição. O erro deixa de depender de memória.',
    'servidor/arquitetura': 'Mudar o próprio script para fazer o passo sozinho (ou gerar o que falta). Em vez de alguém '
                            'lembrar de fazer, o sistema faz — o erro deixa de existir.',
    'checklist': 'Pôr a lição numa lista de conferência obrigatória do fluxo.',
}
SUGESTAO = [  # (padrão no texto, proteção, como)
    (r'pkill|rm -rf|git push|sudo |command not found|matou o pr[oó]prio', 'gancho/validador',
     'gancho que bloqueia o comando antes de rodar, com a mensagem da lição'),
    (r'aus[eê]nt|faltou|pulou|esqueceu|n[aã]o rodou|missing|skipped', 'servidor/arquitetura',
     'o script faz o passo sozinho (ou gera o que falta)'),
    (r'confer|checar|antes de|verificar', 'gancho/validador', 'validador que para antes de seguir'),
    (r'cort|vaz|sobrep|tamanho|limite|teto|caracter|dura[cç]', 'sonda', 'medição automática com o limite'),
]


def sem_acento(t):
    return ''.join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')


def tokens(t):
    return {w for w in re.findall(r'[a-z0-9_]{4,}', sem_acento(t.lower())) if w not in PARADAS}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def sugerir(texto):
    t = sem_acento(texto.lower())
    for padrao, alvo, como in SUGESTAO:
        if re.search(sem_acento(padrao), t):
            return alvo, como
    return 'teste', 'teste que reproduz o erro e falha se ele voltar'


def agrupar(regs, limite=0.34):
    toks = [tokens(r['texto']) for r in regs]
    pai = list(range(len(regs)))

    def raiz(i):
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i
    idx = {}
    for i, ts in enumerate(toks):
        for w in ts:
            idx.setdefault(w, []).append(i)
    comuns = {w for w, l in idx.items() if len(l) > max(8, len(regs) // 40)}
    for w, lista in idx.items():
        if w in comuns:
            continue
        for a in range(len(lista)):
            for b in range(a + 1, len(lista)):
                if jaccard(toks[lista[a]], toks[lista[b]]) >= limite:
                    pai[raiz(lista[a])] = raiz(lista[b])
    grupos = {}
    for i in range(len(regs)):
        grupos.setdefault(raiz(i), []).append(regs[i])
    return list(grupos.values())


def candidatos(cfg):
    """Lista de (vezes, grupo, atual, alvo, como), mais repetido primeiro."""
    arquivos = controle.achar(cfg, 'falhas') + controle.achar(cfg, 'licoes')
    motor = cfg['pauta']['recorrencia']
    if motor and motor != 'interna' and Path(motor).expanduser().is_dir():
        sys.path.insert(0, str(Path(motor).expanduser()))
        from aprende.comum import NOME, candidatos as cand_externo, ler_registros  # noqa
        regs = [r for f in arquivos for r in ler_registros(f)]
        return [(v, g, NOME[a], NOME[b], como) for _, g, a, b, como, v in cand_externo(regs)], 'agente-que-aprende'
    regs = [r for f in arquivos for r in controle.registros(f)]
    out = []
    for g in agrupar(regs):
        if len(g) < 2:
            continue
        alvo, como = sugerir(' '.join(r['texto'] for r in g))
        out.append((len(g), g, 'texto', alvo, como))
    out.sort(key=lambda x: -x[0])
    return out, 'interna'


def ancora(grupo):
    """Registro que não muda quando o erro volta: o mais antigo (data, depois arquivo/linha)."""
    def chave(r):
        d = controle.data_de(r.get('data') or '') or controle.data_de(r['texto'])
        return (d.isoformat() if d else '9999', r['arquivo'], -r['linha'])
    return min(grupo, key=chave)
