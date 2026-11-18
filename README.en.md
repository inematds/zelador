# 🔦 Zelador

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Zelador](guia/assets/banner-en.jpg)](https://inematds.github.io/zelador/guia/en/)

**The Zelador agent helps you improve your system every day.** While you sleep, it checks what failed. In the morning, it lets you know. It learns from recurring issues and suggests fixes. You decide.

## 📖 Guide

To understand what it does and how it can change your day (without the technical details): **https://inematds.github.io/zelador/guia/en/**

## What it is

People who leave robots and AI agents working on their own often find out about problems only when someone complains. Zelador is a free program that keeps an eye on things for you: every night, it checks what failed, and every week, it gathers useful improvements into a simple form for you to review. If you don’t already track failures and outstanding tasks, it creates the files. If you do, it uses yours. To install it, just ask your AI.

## What it sees and what it doesn’t

- **Sees:** scheduled tasks running on the computer itself or a Linux server that fail, report errors, or stop running (it learns each task’s normal pattern over a few days); low memory; repeated errors; a nearly full disk; and anything you or your AI record in the failure, limits, and outstanding tasks lists.
- **Doesn’t see:** processes running in online services; system, administrator, or other account tasks; cron jobs without a log file; or incorrect results that leave no trace (unless the failure is recorded).
- **When no one is logged in** (a server, or a computer that has restarted): account schedules only run with `sudo loginctl enable-linger <usuário>`. The diagnostic warns you if this is missing.
- **If no message arrives in the morning, be suspicious:** by default, it sends a line even after a quiet night, so silence may mean the overnight check didn’t run.
- **Sensitive data:** the alert and report may include excerpts from logs, and the AI explanation sends the title, proposal, and evidence. If your logs contain customer data, set `noite.trechos = false` and leave `explicar.comando` empty.
- Cron jobs are only monitored through what appears in the log file: use `>> arquivo.log 2>&1`.
- If it can’t check something, the alert says what it couldn’t check instead of saying the night was quiet.
- Alerts are sent only after you choose a channel. The form opens on the computer where Zelador is running. To open it on your phone, connect both devices to a private network and add the address to `painel.enderecos` and `painel.link`.
- Tested on Linux. Mac and Windows have not been tested yet.

## How to get started (no technical skills needed)

Open Claude Code or Codex on the machine where the tasks run, in the folder where your projects are stored, and paste:

```text
Read the Zelador project at https://github.com/inematds/zelador (the README explains everything, including installation).
Download a copy to a temporary folder, outside my projects, and run only the diagnostic from the folder where my projects are stored (look for it if I don’t know). Don’t change anything.
Then explain in plain English:
1. Can it see the tasks running here? What would it see, what wouldn’t it see, and would it keep running with no one logged in?
2. What do I already have that it can use?
3. What’s missing that it would create?
4. Where would I receive alerts, and what would I need to do for that?
Don’t install or change anything yet. Show me the plan and wait for me to say yes.
When I say yes, install it in a permanent folder, never the temporary one.
```

---

## Technical installation

Python 3.11+, standard library only. Tested on Linux; sources that aren’t available on the machine (no `journalctl`, no cron) are skipped and reported as skipped. No API: AI explanations are optional and use the command you choose (for example, `claude -p` with your subscription).

```bash
git clone https://github.com/inematds/zelador.git && cd zelador
python3 -m unittest discover -s tests -v     # 23 testes, sem rede
bin/zelador iniciar                          # diagnóstico: não escreve nada
bin/zelador iniciar --aplicar                # cria o que falta, nunca sobrescreve
bin/zelador bloco                            # instrução para colar no CLAUDE.md/AGENTS.md
bin/zelador agendar --aplicar                # (clone numa pasta permanente) madrugada 04:20, pauta segunda 07:45, painel sempre ligado
```

The diagnostic reports each item separately:

| Output | Meaning |
|---|---|
| `✓ JÁ TEM` | Zelador uses it as is |
| `→ PROPOSTA` | You have something similar or can enable a source; it explains and lets you decide |
| `+ CRIAR` | Nothing exists; with `--aplicar` it creates the file from the template |

A similar filename (`ERRORS.md`, `TODO.md`) is adopted by `--aplicar` only when you don’t already have a file of that type. If you do, it stays as a suggestion.

## The process, from beginning to end

🧠 you · ⚙️ script/timer · 🤖 AI (optional)

| # | Step | Command | Who |
|---|---|---|---|
| 1 | See what you already have and what’s missing | `zelador iniciar` | 🧠 |
| 2 | Create what’s missing and map what you already use | `zelador iniciar --aplicar` | ⚙️ |
| 3 | Tell the agent to record failures, limits, and outstanding tasks (paste into CLAUDE.md/AGENTS.md) | `zelador bloco` | 🧠 |
| 4 | Choose the alert (Telegram, desktop, or none) and, if you like, the AI that explains things | edit `~/.config/zelador/zelador.toml` | 🧠 |
| 5 | Schedule | `zelador agendar --aplicar` | ⚙️ |
| 6 | Every day at 04:20: task failures, low memory, repeated errors, cron errors, new logs, disk | `zelador noite` | ⚙️ |
| 7 | Every Monday at 07:45: agenda with recurring failures, serious overnight issues, your other monitors, open limits, and stalled outstanding tasks | `zelador pauta --avisar` | ⚙️ |
| 8 | Every new item gets a plain explanation: what happened, why it matters, and what the proposal does | `explicar.comando` | 🤖 |
| 9 | Review and decide in the dashboard: Approve, Reject (hidden for 8 weeks), Analyze, Postpone, with a note | `zelador painel` → http://127.0.0.1:8810/ | 🧠 |
| 10 | Wrap up the week: approved and “analyze” items are added to the outstanding tasks, and the alert shares the results | button in the dashboard | 🧠 |

## Where everything is stored

- Configuration: `~/.config/zelador/zelador.toml` (commented example in `exemplos/zelador.toml`).
- Data: `~/.local/share/zelador/` — `noite/` (overnight reports), `pautas/`, `decisoes.json`, `explicacoes.json`.
- Templates for files it creates: `zelador/modelos/`.
- Telegram alerts: `zelador/modelos/avisar-telegram.sh` (keep the token in one of your own files, never in the repository).
- Demo agenda with made-up data: `exemplos/pauta-demo.json`.

## Security

- The diagnostic only reads. `--aplicar` creates files that don’t exist and saves the previous config as `.toml.antes`.
- It never edits your CLAUDE.md/AGENTS.md: it shows you the block to paste.
- The dashboard listens only on `127.0.0.1`; use another address (VPN) only if you add it to `painel.enderecos`.
- `tests/test_sem_dados_sensiveis.py` rejects versioned home paths, IP addresses, email addresses, tokens, and personal configuration or data.

## License

MIT.