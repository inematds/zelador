"""Aviso: roda o comando configurado com a mensagem como último argumento. Sem comando, não avisa."""
import subprocess


def avisar(cfg, mensagem):
    cmd = cfg['aviso']['comando']
    if not cmd:
        return 'sem comando de aviso configurado (só relatório)'
    try:
        r = subprocess.run([*cmd, mensagem[:3800]], capture_output=True, text=True, timeout=60)
        return (r.stdout or r.stderr).strip()[:200] or f'saída {r.returncode}'
    except Exception as e:
        return f'aviso falhou: {e}'
