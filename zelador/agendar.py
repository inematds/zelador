"""Agendamento: timers do systemd do usuário (ou linhas de cron, se não houver systemd)."""
import shutil
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BIN = RAIZ / 'bin' / 'zelador'
UNIDADES = Path('~/.config/systemd/user').expanduser()


def unidades(config_arq):
    env = f'Environment=ZELADOR_CONFIG={config_arq}\n'
    return {
        'zelador-noite.service': f'[Unit]\nDescription=zelador: madrugada (erros graves e repetidos das últimas 24 h)\n\n'
                                 f'[Service]\nType=oneshot\n{env}ExecStart={BIN} noite\nTimeoutStartSec=10min\n'
                                 f'MemoryMax=1G\nNice=10\n',
        'zelador-noite.timer': '[Unit]\nDescription=zelador: madrugada todo dia às 04:20\n\n[Timer]\n'
                               'OnCalendar=*-*-* 04:20:00\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n',
        'zelador-pauta.service': f'[Unit]\nDescription=zelador: pauta semanal e aviso com o link do painel\n\n'
                                 f'[Service]\nType=oneshot\n{env}ExecStart={BIN} pauta --avisar\n'
                                 f'TimeoutStartSec=20min\nMemoryMax=1G\nNice=10\n',
        'zelador-pauta.timer': '[Unit]\nDescription=zelador: pauta toda segunda às 07:45\n\n[Timer]\n'
                               'OnCalendar=Mon 07:45\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n',
        'zelador-painel.service': f'[Unit]\nDescription=zelador: painel da pauta semanal\nAfter=network-online.target\n\n'
                                  f'[Service]\n{env}ExecStart={BIN} painel\nRestart=on-failure\nRestartSec=30\n'
                                  f'MemoryMax=256M\n\n[Install]\nWantedBy=default.target\n',
    }


def plano(config_arq):
    if shutil.which('systemctl'):
        return 'systemd', [f'{UNIDADES / n}' for n in unidades(config_arq)]
    return 'cron', [f'20 4 * * * ZELADOR_CONFIG={config_arq} {BIN} noite',
                    f'45 7 * * 1 ZELADOR_CONFIG={config_arq} {BIN} pauta --avisar',
                    f'@reboot ZELADOR_CONFIG={config_arq} {BIN} painel']


def aplicar(config_arq):
    modo, itens = plano(config_arq)
    if modo == 'cron':
        return ['sem systemd: acrescente estas linhas com `crontab -e`:'] + itens
    UNIDADES.mkdir(parents=True, exist_ok=True)
    feitos = []
    for nome, txt in unidades(config_arq).items():
        p = UNIDADES / nome
        if p.exists() and p.read_text() != txt:
            p.with_suffix(p.suffix + '.antes').write_text(p.read_text())
            feitos.append(f'cópia de {nome} em {nome}.antes')
        p.write_text(txt)
        feitos.append(f'escrito {p}')
    subprocess.run(['systemctl', '--user', 'daemon-reload'])
    r = subprocess.run(['systemctl', '--user', 'enable', '--now', 'zelador-noite.timer', 'zelador-pauta.timer',
                        'zelador-painel.service'], capture_output=True, text=True)
    feitos.append('ativado: zelador-noite.timer, zelador-pauta.timer, zelador-painel.service'
                  if r.returncode == 0 else f'falhou ao ativar: {r.stderr.strip()[:200]}')
    return feitos
