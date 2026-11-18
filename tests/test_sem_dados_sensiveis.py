"""Trava: nada da máquina de quem desenvolve nem segredo entra no repositório.

Falha se um arquivo versionado tiver caminho de casa, IP que não seja local, e-mail, cara de token/chave,
ou se a config/dados da pessoa (zelador.toml fora de exemplos/, .env, decisoes.json…) forem versionados.
"""
import re
import subprocess
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PROIBIDO = [
    (r'/home/[a-z_][a-z0-9_-]*/|/Users/[A-Za-z0-9_-]+/', 'caminho de casa'),
    (r'\b(?!127\.0\.0\.1\b|0\.0\.0\.0\b)(?:\d{1,3}\.){3}\d{1,3}\b', 'IP'),
    (r'[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]{2,}', 'e-mail'),
    (r'\bsk-[A-Za-z0-9_-]{16,}|\bghp_[A-Za-z0-9]{20,}|\bxox[bpa]-[A-Za-z0-9-]{10,}|\b\d{8,10}:[A-Za-z0-9_-]{30,}'
     r'|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY', 'token/chave'),
]
ARQUIVO_PROIBIDO = re.compile(r'(^|/)(\.env[^/]*|decisoes\.json|explicacoes\.json|estado[^/]*\.json|telegram\.env)$'
                              r'|^(?!exemplos/).*zelador\.toml$')


def versionados():
    r = subprocess.run(['git', 'ls-files'], cwd=RAIZ, capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l] if r.returncode == 0 else []


class SemDadosSensiveis(unittest.TestCase):
    def test_conteudo(self):
        achados = []
        for nome in versionados():
            if nome == 'tests/test_sem_dados_sensiveis.py':
                continue
            p = RAIZ / nome
            try:
                txt = p.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            for n, linha in enumerate(txt.splitlines(), 1):
                for padrao, rotulo in PROIBIDO:
                    if re.search(padrao, linha):
                        achados.append(f'{nome}:{n} {rotulo}: {linha.strip()[:90]}')
        self.assertEqual(achados, [], 'dado sensível no repositório:\n' + '\n'.join(achados))

    def test_arquivos(self):
        ruins = [n for n in versionados() if ARQUIVO_PROIBIDO.search(n)]
        self.assertEqual(ruins, [], f'config/dados da pessoa versionados: {ruins}')


if __name__ == '__main__':
    unittest.main()
