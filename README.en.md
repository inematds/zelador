# 🔦 Zelador

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Zelador](guia/assets/banner-en.jpg)](https://inematds.github.io/zelador/guia/en/)

**The Zelador agent helps you improve your system every day.** Without it, you only find out about problems when someone complains. With it, your machine’s routines are checked every night, and in the morning it lets you know. If you turn on explanations from your AI, it investigates the cause and suggests a fix. You decide and ask the AI to do it.

## 📖 Guide

To understand what it does and how it changes your day (without the technical details): **https://inematds.github.io/zelador/guia/en/**

## What it is

People who leave robots and AI agents working on their own only find out about problems when someone complains. Zelador is a free program that keeps an eye on them for you: every night it checks what failed, and every week it gathers what’s worth improving into a simple form for you to decide. If you don’t already track failures and pending items, it creates the files. If you do, it uses yours. To install it, just ask your AI.

## What it sees and what it doesn’t

- **Sees:** scheduled routines on the computer itself or a Linux server that fail, write an error, or stop running (it determines each routine’s schedule from the machine’s history), low memory, repeated errors, a nearly full disk, and everything you or your AI record in the failure, limit, and pending item lists.
- **Doesn’t see:** what runs on internet services; system, administrator, or other account routines; cron jobs without a log file; or incorrect results that leave no trace (unless the failure is recorded).
- **When nobody is logged in** (server, or a computer that has restarted): account schedules only run with `sudo loginctl enable-linger <usuário>`. The diagnostic warns you if this is missing.
- **If no message arrives in the morning, be suspicious:** by default it sends a line even after a quiet night, so silence means the round may not have run.
- **Sensitive data:** the notification and report may include excerpts from logs, and AI explanations send the title, proposal, and evidence. If logs contain customer data, use `noite.trechos = false` and leave `explicar.comando` empty.
- Cron jobs are only visible through what appears in the log file: use `>> arquivo.log 2>&1`.
- If it can’t check something, the notification says what it couldn’t check instead of saying the night was quiet.
- Notifications are sent only after you choose a channel. The form opens on the computer where Zelador is running, and its address appears in every overnight report; to open it on your phone, connect both devices to a private network and add the address to `painel.enderecos` and `painel.link`.
- Tested on Linux. Mac and Windows haven’t been tested yet.

## How to get started (without being technical)

Open Claude Code or Codex on the machine where the routines run, in the folder where your projects are, and paste:

```text
Read the Zelador project at https://github.com/inematds/zelador (the README explains everything, including installation).
Download a copy to a temporary folder, outside my projects, and run only the diagnostic from the folder where my projects are (look for it; if I don’t have one, continue without it). Don’t change anything.
Then answer me in plain English:
1. Can it see the routines running here? What would it see, what wouldn’t it see, and will it keep running when nobody is logged in?
2. What do I already have that it can use?
3. What’s missing that it would create?
4. Where would I receive notifications, and what would I need to do for that?
Don’t install or change anything yet. Show me the plan and wait for me to say yes.
When I say yes, install it in a permanent folder, never the temporary one.
```

---

## Technical installation

Python 3.11+, standard library only. Tested on Linux; sources that aren’t available on the machine (no `journalctl`, no cron) are skipped and shown as skipped in the report. No API: AI explanations are optional and use the command you choose (for example, `claude -p` with your subscription).

```bash
git clone https://github.com/inematds/zelador.git && cd zelador
python3 -m unittest discover -s tests -v     # 27 tests, sem rede
bin/zelador iniciar                          # diagnóstico: não escreve nada
bin/zelador iniciar --aplicar                # cria o que falta, nunca sobrescreve
bin/zelador bloco                            # instrução para colar no CLAUDE.md/AGENTS.md
bin/zelador agendar --aplicar                # (clone numa pasta permanente) madrugada 04:20, pauta segunda 07:45, painel sempre ligado
```

The diagnostic reports each item individually:

| Output | Meaning |
|---|---|
| `✓ JÁ TEM` | Zelador uses it as is |
| `→ PROPOSTA` | You have something similar, or can enable a source; it explains and you decide |
| `+ CRIAR` | Nothing exists; with `--aplicar` it creates one from the template |

A similar filename (`ERRORS.md`, `TODO.md`) is adopted by `--aplicar` only if you don’t already have a file of that type. If you do, it remains a suggestion.

## The process, from start to finish

🧠 you · ⚙️ script/timer · 🤖 AI (optional)

| # | Step | Command | Who |
|---|---|---|---|
| 1 | See what you already have and what’s missing | `zelador iniciar` | 🧠 |
| 2 | Create what’s missing and map what you already use | `zelador iniciar --aplicar` | ⚙️ |
| 3 | Tell the agent to record failures, limits, and pending items (paste into CLAUDE.md/AGENTS.md) | `zelador bloco` | 🧠 |
| 4 | Choose notifications (Telegram, desktop, or none) and, if you like, the AI that explains | edit `~/.config/zelador/zelador.toml` | 🧠 |
| 5 | Schedule | `zelador agendar --aplicar` | ⚙️ |
| 6 | Every day at 04:20: routine failures, low memory, repeated errors, cron errors, new logs, disk | `zelador noite` | ⚙️ |
| 7 | Every Monday at 07:45: agenda with recurring failures, serious overnight issues, your other monitors, open limits, and stalled pending items | `zelador pauta --avisar` | ⚙️ |
| 8 | Each new item gets a plain explanation, likely cause, and suggested fix, by reading the end of routine logs and recent project logs, trying to hide passwords, with no guarantee (`explicar.ler_registros`) | `explicar.comando` | 🤖 |
| 9 | Read and decide in the panel: Approve, Reject (hidden for 8 weeks), Investigate, Postpone, with a note | `zelador painel` → http://127.0.0.1:8810/ | 🧠 |
| 10 | Close the week: approved and “investigate” items go into pending items, and the notification sends the score | button in the panel | 🧠 |

## Where everything lives

- Configuration: `~/.config/zelador/zelador.toml` (commented example in `exemplos/zelador.toml`).
- Data: `~/.local/share/zelador/` — `noite/` (overnight reports), `pautas/`, `decisoes.json`, `explicacoes.json`.
- Templates for the files it creates: `zelador/modelos/`.
- Telegram notifications: `zelador/modelos/avisar-telegram.sh` (token in one of your files, never in the repository).
- Demo agenda, with made-up data: `exemplos/pauta-demo.json`.

## Security

- The diagnostic only reads. `--aplicar` creates files that don’t exist and saves the previous config as `.toml.antes`.
- It never edits your CLAUDE.md/AGENTS.md: it shows the block for you to paste.
- The panel listens only on `127.0.0.1`; another address (VPN) only if you add it to `painel.enderecos`.
- `tests/test_sem_dados_sensiveis.py` rejects versioned home paths, IPs, email addresses, tokens, and personal configuration or data.

## License

MIT.