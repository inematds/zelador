import collections
import datetime as dt
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zelador import config, iniciar, noite, painel, pauta


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


class NoiteSemFontes(Base):
    def test_nao_diz_limpa_sobre_o_que_nao_olhou(self):
        msgs = []
        with mock.patch('zelador.noite.shutil.which', return_value=None), \
                mock.patch('zelador.avisar.avisar', side_effect=lambda c, m: msgs.append(m) or 'ok'):
            r = noite.rodar(self.cfg)
        self.assertEqual(sorted(r['nao_verificado']), ['cron', 'journal'])
        self.assertNotIn('limpa', msgs[0])
        self.assertIn('Não consegui verificar', msgs[0])


class NoiteCronSemLog(Base):
    def test_tarefa_sem_log_aparece_como_nao_verificada(self):
        msgs = []

        def falso(cmd, timeout=120):
            return '0 3 * * * /bin/backup\n' if cmd[0] == 'crontab' else ''
        with mock.patch('zelador.noite.sh', side_effect=falso), \
                mock.patch('zelador.noite.journal', return_value=({}, {}, {}, [], True, {})) as j, \
                mock.patch('zelador.avisar.avisar', side_effect=lambda c, m: msgs.append(m) or 'ok'):
            import collections
            j.return_value = (collections.Counter(), collections.Counter(), {}, [], True, {})
            r = noite.rodar(self.cfg)
        self.assertIn('cron', r['nao_verificado'])
        self.assertNotIn('limpa', msgs[0])


class NoiteLogs(Base):
    def test_erro_em_portugues_no_log_com_variavel_e_aviso_mostra(self):
        log = self.home / 'backup.log'
        log.write_text('Erro: falha ao copiar\n')
        msgs = []

        def falso(cmd, timeout=120):
            return '0 3 * * * /bin/backup >> $HOME/backup.log 2>&1\n' if cmd[0] == 'crontab' else ''
        vazio = (collections.Counter(), collections.Counter(), {}, [], True, {})
        with mock.patch('zelador.noite.sh', side_effect=falso), mock.patch('zelador.noite.journal', return_value=vazio), \
                mock.patch('zelador.noite.oom_kernel', return_value=[]), \
                mock.patch('zelador.noite.shutil.which', return_value='/bin/x'), \
                mock.patch('zelador.avisar.avisar', side_effect=lambda c, m: msgs.append(m) or 'ok'):
            noite.rodar(self.cfg)
        self.assertIn('backup.log', msgs[0])
        self.assertNotIn('Não consegui verificar', msgs[0])


class SemTrechos(Base):
    def test_trechos_desligados_nao_saem_no_aviso(self):
        self.cfg['noite']['trechos'] = False
        log = self.home / 'a.log'
        log.write_text('Erro: paciente Maria sem cadastro\n')
        msgs = []

        def falso(cmd, timeout=120):
            return f'0 3 * * * /bin/x >> {log} 2>&1\n' if cmd[0] == 'crontab' else ''
        vazio = (collections.Counter(), collections.Counter(), {}, [], True, {})
        with mock.patch('zelador.noite.sh', side_effect=falso), mock.patch('zelador.noite.journal', return_value=vazio), \
                mock.patch('zelador.noite.shutil.which', return_value='/bin/x'), \
                mock.patch('zelador.avisar.avisar', side_effect=lambda c, m: msgs.append(m) or 'ok'):
            r = noite.rodar(self.cfg)
        self.assertIn('a.log', msgs[0])
        self.assertNotIn('Maria', msgs[0])
        self.assertNotIn('Maria', Path(r['relatorio']).read_text())


class RotinaParada(Base):
    def falso(self, timers):
        def sh(cmd, timeout=120):
            if '--output=json' in cmd:
                return json.dumps(timers)
            if 'list-unit-files' in cmd:
                return 'backup.timer enabled enabled\n'
            return ''
        return sh

    def test_aprende_o_ritmo_e_aponta_a_que_parou(self):
        dia, agora, estado = 86400, 10_000_000, {}
        for n in (4, 3, 2):
            with mock.patch('zelador.noite.sh', side_effect=self.falso([{'unit': 'backup.timer', 'last': (agora - n * dia) * 1_000_000}])):
                self.assertEqual(noite.rotinas_paradas(estado, agora - n * dia + 60), [])
        with mock.patch('zelador.noite.sh', side_effect=self.falso([{'unit': 'backup.timer', 'last': (agora - 2 * dia) * 1_000_000}])):
            self.assertEqual(noite.rotinas_paradas(estado, agora), [])  # dentro da folga
            achou = noite.rotinas_paradas(estado, agora + 2 * dia)
        self.assertEqual(achou[0][0], 'backup')

    def test_rotina_que_termina_bem_mas_escreveu_erro_aparece(self):
        msgs = []
        vazio = (collections.Counter(), collections.Counter(), {}, [], True, {'backup.service': (2, 'ERRO ao copiar')})

        def sh(cmd, timeout=120):
            return 'x y backup.timer backup.service\n' if 'list-timers' in cmd and '--output=json' not in cmd else ''
        with mock.patch('zelador.noite.sh', side_effect=sh), mock.patch('zelador.noite.journal', return_value=vazio), \
                mock.patch('zelador.noite.oom_kernel', return_value=[]), \
                mock.patch('zelador.avisar.avisar', side_effect=lambda c, m: msgs.append(m) or 'ok'):
            noite.rodar(self.cfg)
        self.assertIn('a rotina backup terminou, mas escreveu 2 linha(s) com erro', msgs[0])


class ErroNoLog(unittest.TestCase):
    def test_frase_negada_nao_e_erro(self):
        for ok in ('backup concluido sem erro', 'nenhum erro encontrado', 'nenhuma falha', '0 failed', 'no errors'):
            self.assertFalse(noite.tem_erro(ok), ok)
        for ruim in ('Erro: falha ao copiar', 'ERROR disk', 'backup falhou'):
            self.assertTrue(noite.tem_erro(ruim), ruim)


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
