# zelador

Leia o README.md. Python 3.11+, só biblioteca padrão.
Testar: `python3 -m unittest discover -s tests -v`.
Nada específico de uma máquina no código (caminhos, IPs, bots, nomes de projeto): isso vai na config da pessoa.
O diagnóstico só lê; escrever só com `--aplicar` e nunca sobrescrever arquivo existente.
Nenhuma chamada de API no código. IA só pelo `explicar.comando` que a pessoa configurar.
Versão em `zelador/config.py` (VERSAO) e no CHANGELOG.md, semver `X.YY.ZZ` sem zerar os de baixo no minor.
Autor e committer: inematds <inematds@gmail.com>. Publicação via git.
