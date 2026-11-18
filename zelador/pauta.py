"""Pauta semanal: junta as propostas de melhoria da semana para a pessoa decidir no painel.

Fontes (cada uma só entra se existir):
  falhas que voltam   — FALHAS/LIÇÕES de todos os projetos (motor interno ou agente-que-aprende)
  madrugadas          — o que a vigia da madrugada marcou como GRAVE nas últimas 7 noites
  <relatórios>        — último .md de outro monitor que a pessoa já tem (config pauta.relatorios)
  <grupos>            — FALHAS novos da semana num grupo de projetos (config pauta.grupos)
  limites             — LIMITES com status 'aberto'
  pendências paradas  — '- [ ]' com data mais velha que N dias
"""
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path

from . import avisar, config, controle, recorrencia

FONTE_SIMPLES = {
    'madrugadas': 'Uma rotina automática falhou de madrugada ou faltou memória. A proposta é abrir o log, achar a '
                  'causa e pôr a proteção que falta (teto, nova tentativa, conferência) para não cair de novo.',
    'limites': 'Algo te barrou (ferramenta, permissão, cota, ambiente). A proposta é o caminho para destravar de vez, '
               'em vez de contornar toda vez.',
    'pendências paradas': 'Isto está nas pendências há semanas sem andar. A proposta é decidir: fazer agora, marcar '
                          'uma data ou fechar.',
    'relatorio': 'Outro monitor seu registrou estes casos na semana. A proposta é ver se é sempre o mesmo motivo e '
                 'transformar isso numa regra ou trava do fluxo.',
    'grupo': 'Falhas novas deste grupo de projetos na semana. A proposta é conferir se alguma chega a quem usa o '
             'sistema e se a correção já tem teste.',
}

PEDIDO = """Você explica, em português do Brasil simples, propostas de melhoria de um sistema de automação para
o dono dele, que decide se aprova. Sem jargão: se um termo técnico for inevitável, explique-o na mesma frase.
Use "você". Frases curtas, concretas, sem exagero.

Para CADA item abaixo, devolva:
- "aconteceu": o que deu errado, em 1–2 frases, como se contasse para alguém de fora.
- "importa": por que isso atrapalha (tempo perdido, entrega que não sai, risco, retrabalho), 1 frase.
- "muda": o que a proposta faria na prática e o que mudaria para você depois, 1–2 frases.

Responda SOMENTE com um objeto JSON: {"<id>": {"aconteceu": "...", "importa": "...", "muda": "..."}, ...}
Itens:
"""


def ident(*partes):
    base = '|'.join(re.sub(r'\d+', '#', p.lower())[:90] for p in partes)
    return hashlib.sha1(base.encode()).hexdigest()[:10]


def item(fonte, titulo, proposta, evidencia, gravidade='média', chave=None, **extra):
    return {'id': ident(fonte, chave or titulo), 'fonte': fonte, 'titulo': titulo.strip(), 'proposta': proposta,
            'evidencia': evidencia, 'gravidade': gravidade, **extra}


def de_recorrencia(cfg):
    cands, motor = recorrencia.candidatos(cfg)
    out = []
    for vezes, g, atual, alvo, como in cands[:cfg['pauta']['top']]:
        g = sorted(g, key=lambda r: (r['arquivo'], r['linha']))
        base = recorrencia.ancora(g)
        projs = sorted({Path(r['arquivo']).parent.name for r in g})
        ev = [f"{r['data']} · {Path(r['arquivo']).parent.name}/{Path(r['arquivo']).name}:{r['linha']} — "
              f"{r['problema'][:220]} → correção: {r['correcao'][:160]}" for r in g[:6]]
        simples = (f'Este erro já aconteceu {vezes} vezes. Hoje a correção está '
                   f'{recorrencia.HOJE.get(atual, atual)}. Proposta: {recorrencia.PROPOSTA.get(alvo, como)}')
        out.append(item('falhas que voltam', base['problema'][:140], f'Subir de {atual} para {alvo}: {como}.', ev,
                        'alta' if vezes >= 4 else 'média', chave=base['problema'], vezes=vezes, projetos=projs,
                        proposta_simples=simples, motor=motor))
    return out


def de_madrugadas(cfg, hoje):
    pasta = config.dados(cfg, 'noite')
    cont, noites = {}, 0
    for i in range(7):
        d = hoje - dt.timedelta(days=i)
        pj, pm = pasta / f'{d:%F}.json', pasta / f'{d:%F}.md'
        if pj.is_file():
            graves = json.loads(pj.read_text()).get('grave', [])
        elif pm.is_file():
            bloco = pm.read_text().split('## Grave', 1)[-1].split('## Atenção', 1)[0]
            graves = [l[2:] for l in bloco.splitlines() if l.startswith('- ') and l != '- nada']
        else:
            continue
        noites += 1
        for g in graves:
            chave = re.sub(r'\d+×', 'N×', re.sub(r'\d+ processo', 'N processo', g))
            cont.setdefault(chave, []).append(f'{d:%d/%m}: {g}')
    return [item('madrugadas', k[:140], 'Ver o log, achar a causa e pôr a proteção que falta; registrar no FALHAS.md.',
                 ev, 'alta' if len(ev) >= 2 else 'média', vezes=len(ev), noites=noites) for k, ev in cont.items()]


def de_relatorios(cfg):
    out = []
    for r in cfg['pauta']['relatorios']:
        pasta = Path(r['pasta']).expanduser()
        rels = sorted(pasta.glob('*.md')) if pasta.is_dir() else []
        if not rels:
            continue
        for secao in re.split(r'\n## ', rels[-1].read_text())[1:]:
            nome, *linhas = secao.splitlines()
            reais = [l[2:] for l in linhas if l.startswith('- ') and not re.match(r'- (nenhum|nenhuma|nada)\b', l)]
            if reais:
                out.append(item(r['nome'], f'{nome}: {len(reais)} caso(s) na semana',
                                'Ver se é sempre o mesmo motivo e virar trava/regra do fluxo.', reais[:8],
                                proposta_simples=FONTE_SIMPLES['relatorio']))
    return out


def de_grupos(cfg, hoje):
    out, limite = [], hoje - dt.timedelta(days=7)
    for gr in cfg['pauta']['grupos']:
        arqs = [p for r in config.raizes(cfg) for p in sorted(r.glob(gr['glob']))]
        achou = False
        for f in arqs:
            novas = [r['problema'][:220] for r in controle.registros(f)
                     if (controle.data_de(r['data'] or '') or dt.date.min) >= limite]
            if novas:
                achou = True
                out.append(item(gr['nome'], f'{f.parent.name}: {len(novas)} falha(s) na semana',
                                'Ver se alguma afeta quem usa e se a correção já tem teste.', novas[:8],
                                'alta' if len(novas) >= 3 else 'média', proposta_simples=FONTE_SIMPLES['grupo']))
        if arqs and not achou:
            out.append(item(gr['nome'], f"{gr['nome']}: nenhuma falha nova na semana",
                            'Só confirmar.', [f"conferidos: {', '.join(p.parent.name for p in arqs)}"], 'baixa',
                            proposta_simples='Nenhuma falha nova registrada nesses projetos. Só confirmar que eles '
                                             'estão sendo usados e registrando — silêncio também pode ser falta de registro.'))
    return out


def de_limites(cfg):
    out = []
    for p in controle.achar(cfg, 'limites'):
        for l in reversed(p.read_text(errors='replace').splitlines()):
            cel = [c.strip() for c in l.strip().strip('|').split('|')]
            if len(cel) >= 6 and cel[-1].lower().startswith('aberto'):
                out.append(item('limites', f'{cel[1][:120]} — barrou: {cel[2][:80]}',
                                cel[4] or 'definir como destravar', [f'{cel[0]} · contorno: {cel[3]}']))
            if len(out) >= cfg['pauta']['limites_max']:
                return out
    return out


def de_pendencias(cfg, hoje):
    out, dias = [], cfg['pauta']['pendencia_parada_dias']
    for p in controle.achar(cfg, 'pendencias'):
        for l in p.read_text(errors='replace').splitlines():
            if not l.startswith('- [ ]'):
                continue
            d = controle.data_de(l[:60])
            if d and (hoje - d).days > dias:
                t = re.sub(r'\*\*', '', l[6:]).strip()
                out.append(item('pendências paradas', t[:140], 'Decidir: fazer agora, adiar com data ou fechar.',
                                [f'parada há {(hoje - d).days} dias', t[:400]], 'baixa'))
            if len(out) >= cfg['pauta']['pendencias_max']:
                return out
    return out


def explicar(cfg, itens, hoje):
    """Explicação simples por item, opcional: cache por id; os que faltam vão em lotes ao comando configurado."""
    arq = config.dados(cfg) / 'explicacoes.json'
    cache = json.loads(arq.read_text()) if arq.is_file() else {}
    e = cfg['explicar']
    faltam = [i for i in itens if i['id'] not in cache and i['fonte'] != 'pendências paradas']
    erro = ''
    if e['comando'] and faltam:
        for k in range(0, min(len(faltam), 10 * e['max_chamadas']), 10):
            lote = [{'id': i['id'], 'fonte': i['fonte'], 'titulo': i['titulo'], 'proposta': i['proposta'],
                     'evidencia': i['evidencia'][:3]} for i in faltam[k:k + 10]]
            try:
                r = subprocess.run(e['comando'], input=PEDIDO + json.dumps(lote, ensure_ascii=False),
                                   capture_output=True, text=True, cwd=Path(e['cwd']).expanduser() if e['cwd'] else None,
                                   timeout=e['timeout'])
                texto, modelo = r.stdout.strip(), '?'
                try:  # EngineBridge e afins devolvem {"status", "texto", "rota"}
                    env = json.loads(texto)
                    if isinstance(env, dict) and 'texto' in env:
                        if env.get('status') not in (None, 'ok'):
                            erro = f"explicar: {env.get('status')}"
                            break
                        texto, modelo = env['texto'], env.get('rota', {}).get('modelo', '?')
                except ValueError:
                    pass
                texto = texto[texto.find('{'):texto.rfind('}') + 1]
                for iid, ex in json.loads(texto).items():
                    if isinstance(ex, dict) and {'aconteceu', 'importa', 'muda'} <= ex.keys():
                        cache[iid] = {**{c: str(ex[c])[:600] for c in ('aconteceu', 'importa', 'muda')},
                                      'modelo': modelo, 'em': f'{hoje:%F}'}
            except Exception as x:
                erro = f'explicar: {x}'
                break
        arq.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
    for i in itens:
        if i['id'] in cache:
            i['explicacao'] = cache[i['id']]
        i.setdefault('proposta_simples', FONTE_SIMPLES.get(i['fonte'], ''))
    return erro


def gerar(cfg, avisar_link=False, sem_ia=False, hoje=None):
    hoje = hoje or dt.date.today()
    arq_dec = config.dados(cfg) / 'decisoes.json'
    dec = json.loads(arq_dec.read_text()) if arq_dec.is_file() else {}
    itens, erros = [], []
    for nome, f in [('falhas que voltam', lambda: de_recorrencia(cfg)), ('madrugadas', lambda: de_madrugadas(cfg, hoje)),
                    ('relatórios', lambda: de_relatorios(cfg)), ('grupos', lambda: de_grupos(cfg, hoje)),
                    ('limites', lambda: de_limites(cfg)), ('pendências', lambda: de_pendencias(cfg, hoje))]:
        try:
            itens += f()
        except Exception as e:  # uma fonte quebrada não derruba a pauta
            erros.append(f'{nome}: {e}')
    visiveis = []
    for it in itens:
        d = dec.get(it['id'])
        if d and d['decisao'] == 'recusar' and \
                (hoje - dt.date.fromisoformat(d['quando'][:10])).days < 7 * cfg['pauta']['recusa_semanas']:
            continue
        if d and d['decisao'] == 'aprovar' and d.get('semana') != f'{hoje:%F}':
            it['ja_aprovado'] = d['quando'][:10]
        visiveis.append(it)
    ordem = {'alta': 0, 'média': 1, 'baixa': 2}
    visiveis.sort(key=lambda x: (ordem[x['gravidade']], -x.get('vezes', 0)))
    if not sem_ia:
        erro = explicar(cfg, visiveis, hoje)
        if erro:
            erros.append(erro)
    else:
        explicar({**cfg, 'explicar': {**cfg['explicar'], 'comando': []}}, visiveis, hoje)
    pauta = {'semana': f'{hoje:%F}', 'gerada': dt.datetime.now().isoformat(timespec='minutes'),
             'erros_fontes': erros, 'itens': visiveis}
    saida = config.dados(cfg, 'pautas') / f'{hoje:%F}.json'
    saida.write_text(json.dumps(pauta, ensure_ascii=False, indent=1))
    alta = sum(i['gravidade'] == 'alta' for i in visiveis)
    res = {'pauta': str(saida), 'itens': len(visiveis), 'alta': alta, 'erros': erros}
    if avisar_link:
        res['aviso'] = avisar.avisar(cfg, f'📋 Pauta da semana {hoje:%d/%m}: {len(visiveis)} proposta(s), {alta} de '
                                          f'prioridade alta.\nLer e decidir (aprovar / recusar / analisar / adiar): '
                                          f'{config.link_painel(cfg)}')
    return res
