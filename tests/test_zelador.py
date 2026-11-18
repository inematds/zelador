import datetime as dt
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zelador import config, iniciar, painel, pauta


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / 'home'
        self.proj = self.home / 'projetos'
        self.proj.mkdir(parents=True)
        self.env = mock.patch.dict(os.environ, {'HOME': str(self.home),
                                                'ZELADOR_CONFIG': str(self.home / '.config/zelador/zelador.toml')})
        self.env.start()
        self.cfg = config.carregar()
        self.cfg['geral']['raizes'] = [str(self.proj)]
        self.cfg['geral']['dados'] = str(self.home / 'dados')

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def estados(self, achados):
        return {(a['peca'], a['estado']) for a in achados}


class PastaVazia(Base):
    def test_propoe_criar_e_so_escreve_com_aplicar(self):
        achados = iniciar.diagnosticar(self.cfg)
        for tipo in ('falhas', 'licoes', 'limites', 'pendencias'):
            self.assertIn((tipo, 'criar'), self.estados(achados))
        self.assertEqual(list(self.proj.iterdir()), [], 'diagnóstico não pode escrever nada')
        iniciar.aplicar(self.cfg, achados)
        self.assertTrue((self.proj / 'FALHAS.md').is_file())
        self.assertTrue((self.proj / 'LIMITES.md').is_file())
        self.assertTrue(Path(self.cfg['_arquivo']).is_file())
        config.carregar()  # o TOML gravado precisa ser válido

    def test_nunca_sobrescreve(self):
        achados = iniciar.diagnosticar(self.cfg)
        (self.proj / 'FALHAS.md').write_text('meu conteúdo')
        iniciar.aplicar(self.cfg, achados)
        self.assertEqual((self.proj / 'FALHAS.md').read_text(), 'meu conteúdo')


class NomesDiferentes(Base):
    def setUp(self):
        super().setUp()
        (self.proj / 'loja/.git').mkdir(parents=True)
        (self.proj / 'loja/ERRORS.md').write_text(
            '| 2026-11-10 | deploy caiu: falta variavel PORT no servidor | conferir env | infra |\n'
            '| 2026-11-14 | deploy caiu de novo: falta variavel PORT no servidor | conferir env antes | infra |\n')
        (self.proj / 'loja/TODO.md').write_text('- [ ] **01/10/2026 — trocar o banco** detalhe\n')

    def test_propoe_mapear_sem_criar_gemeo(self):
        achados = iniciar.diagnosticar(self.cfg)
        self.assertIn(('falhas', 'proposta'), self.estados(achados))
        self.assertNotIn(('falhas', 'criar'), self.estados(achados))
        self.assertNotIn(('pendencias', 'criar'), self.estados(achados))
        iniciar.aplicar(self.cfg, achados)
        self.assertFalse((self.proj / 'FALHAS.md').exists())
        cfg = config.carregar()
        self.assertIn('ERRORS.md', cfg['arquivos']['falhas'])
        self.assertIn('TODO.md', cfg['arquivos']['pendencias'])

    def test_pauta_acha_repeticao_e_pendencia_parada(self):
        self.cfg['arquivos']['falhas'].append('ERRORS.md')
        self.cfg['arquivos']['pendencias'].append('TODO.md')
        res = pauta.gerar(self.cfg, sem_ia=True, hoje=dt.date(2026, 11, 17))
        itens = json.loads(Path(res['pauta']).read_text())['itens']
        fontes = {i['fonte'] for i in itens}
        self.assertEqual(fontes, {'falhas que voltam', 'pendências paradas'})
        self.assertTrue(all(i['proposta_simples'] for i in itens))

    def test_id_estavel_quando_o_erro_volta(self):
        self.cfg['arquivos']['falhas'].append('ERRORS.md')
        antes = pauta.de_recorrencia(self.cfg)[0]['id']
        f = self.proj / 'loja/ERRORS.md'
        f.write_text('| 2026-11-16 | deploy caiu outra vez: falta variavel PORT no servidor | conferir env | infra |\n'
                     + f.read_text())
        self.assertEqual(pauta.de_recorrencia(self.cfg)[0]['id'], antes)


class JaTemPadrao(Base):
    def test_parecido_vira_so_sugestao_quando_ja_tem_o_padrao(self):
        (self.proj / 'a').mkdir()
        (self.proj / 'a/FALHAS.md').write_text('| 2026-11-10 | x quebrou feio | y | infra |\n')
        (self.proj / 'b').mkdir()
        (self.proj / 'b/bugs.md').write_text('coisas')
        achados = iniciar.diagnosticar(self.cfg)
        sug = [a for a in achados if a['peca'] == 'falhas' and a['estado'] == 'proposta']
        self.assertTrue(sug and all(a['acao'] is None for a in sug))
        iniciar.aplicar(self.cfg, achados)
        self.assertNotIn('bugs.md', config.carregar()['arquivos']['falhas'])


class Painel(NomesDiferentes):
    def test_decidir_recusar_some_e_fechar_vai_para_pendencias(self):
        self.cfg['arquivos']['falhas'].append('ERRORS.md')
        self.cfg['arquivos']['pendencias'].append('TODO.md')
        hoje = dt.date.today()
        pauta.gerar(self.cfg, sem_ia=True, hoje=hoje)
        itens = painel.pauta_atual(self.cfg)['itens']
        falha = next(i for i in itens if i['fonte'] == 'falhas que voltam')
        pend = next(i for i in itens if i['fonte'] == 'pendências paradas')
        self.assertIsNone(painel.decidir(self.cfg, {'id': 'nao-existe', 'decisao': 'aprovar'}))
        self.assertIsNone(painel.decidir(self.cfg, {'id': falha['id'], 'decisao': 'apagar-tudo'}))
        painel.decidir(self.cfg, {'id': falha['id'], 'decisao': 'aprovar', 'nota': 'fazer o teste'})
        painel.decidir(self.cfg, {'id': pend['id'], 'decisao': 'recusar', 'nota': ''})
        r = painel.fechar(self.cfg)
        self.assertEqual(r['enviados'], 1)
        txt = (self.proj / 'loja/TODO.md').read_text()
        self.assertIn('Fazer [falhas que voltam]', txt)
        self.assertIn('fazer o teste', txt)
        self.assertEqual(painel.fechar(self.cfg)['enviados'], 0, 'fechar de novo não duplica')
        pauta.gerar(self.cfg, sem_ia=True, hoje=hoje)
        ids = {i['id'] for i in painel.pauta_atual(self.cfg)['itens']}
        self.assertNotIn(pend['id'], ids, 'recusado some da pauta')


class Explicar(NomesDiferentes):
    def test_comando_externo_e_cache(self):
        self.cfg['arquivos']['falhas'].append('ERRORS.md')
        script = self.home / 'explica.py'
        script.write_text('import sys,json\nitens=json.loads(sys.stdin.read().split("Itens:\\n",1)[1])\n'
                          'print(json.dumps({"status":"ok","texto":json.dumps({i["id"]:{"aconteceu":"a","importa":"b",'
                          '"muda":"c"} for i in itens}),"rota":{"modelo":"falso"}}))\n')
        self.cfg['explicar']['comando'] = ['python3', str(script)]
        res = pauta.gerar(self.cfg, hoje=dt.date(2026, 11, 17))
        itens = json.loads(Path(res['pauta']).read_text())['itens']
        com = [i for i in itens if 'explicacao' in i]
        self.assertTrue(com and com[0]['explicacao']['modelo'] == 'falso')
        self.cfg['explicar']['comando'] = ['false']  # cache: não chama de novo
        res = pauta.gerar(self.cfg, hoje=dt.date(2026, 11, 17))
        self.assertEqual(res['erros'], [])


if __name__ == '__main__':
    unittest.main()
