"""zelador — vigia a madrugada, junta as propostas da semana e te deixa decidir num formulário.

  zelador iniciar [--raiz DIR] [--aplicar]   diagnóstico: o que já tem, o que propõe, o que cria
  zelador bloco                              instrução para colar no CLAUDE.md/AGENTS.md
  zelador noite [--sem-aviso] [--horas N]    vigia da madrugada
  zelador pauta [--avisar] [--sem-ia]        pauta da semana
  zelador painel                             formulário de decisão (aprovar/recusar/analisar/adiar)
  zelador agendar [--aplicar]                timers (systemd do usuário) ou linhas de cron
  zelador versao
"""
import argparse
import json
import sys
from pathlib import Path

from . import agendar, config, iniciar, noite, painel, pauta


def main(argv=None):
    ap = argparse.ArgumentParser(prog='zelador', description=__doc__.split('\n')[0])
    ap.add_argument('--config', help='arquivo TOML (padrão ~/.config/zelador/zelador.toml ou $ZELADOR_CONFIG)')
    sub = ap.add_subparsers(dest='acao', required=True)
    s = sub.add_parser('iniciar')
    s.add_argument('--raiz')
    s.add_argument('--aplicar', action='store_true')
    sub.add_parser('bloco')
    s = sub.add_parser('noite')
    s.add_argument('--sem-aviso', action='store_true')
    s.add_argument('--horas', type=int)
    s = sub.add_parser('pauta')
    s.add_argument('--avisar', action='store_true')
    s.add_argument('--sem-ia', action='store_true')
    sub.add_parser('painel')
    s = sub.add_parser('agendar')
    s.add_argument('--aplicar', action='store_true')
    sub.add_parser('versao')
    a = ap.parse_args(argv)
    cfg = config.carregar(a.config)

    if a.acao == 'versao':
        print(config.VERSAO)
    elif a.acao == 'bloco':
        print((Path(iniciar.__file__).with_name('modelos') / 'bloco-instrucoes.md').read_text())
    elif a.acao == 'iniciar':
        if a.raiz:
            cfg['geral']['raizes'] = [a.raiz]
        achados = iniciar.diagnosticar(cfg)
        print(iniciar.texto(achados))
        if a.aplicar:
            print('\n' + '\n'.join(f'feito: {f}' for f in iniciar.aplicar(cfg, achados, a.raiz)))
        else:
            print('\nNada foi escrito. Para criar o que está em "+ CRIAR" e aceitar as propostas de mapeamento: '
                  '`zelador iniciar --aplicar`')
    elif a.acao == 'noite':
        print(json.dumps(noite.rodar(cfg, a.horas, a.sem_aviso), ensure_ascii=False))
    elif a.acao == 'pauta':
        print(json.dumps(pauta.gerar(cfg, a.avisar, a.sem_ia), ensure_ascii=False))
    elif a.acao == 'painel':
        return painel.servir(cfg)
    elif a.acao == 'agendar':
        modo, itens = agendar.plano(cfg['_arquivo'])
        if a.aplicar:
            print('\n'.join(agendar.aplicar(cfg['_arquivo'])))
        else:
            print(f'Plano ({modo}):\n' + '\n'.join(f'  {i}' for i in itens) + '\nPara instalar: `zelador agendar --aplicar`')
    return 0


if __name__ == '__main__':
    sys.exit(main())
