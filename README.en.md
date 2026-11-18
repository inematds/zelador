# 🔦 Zelador

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Zelador](guia/assets/banner-en.jpg)](https://inematds.github.io/zelador/guia/en/)

**Did your automation fail overnight without anyone noticing?** With Zelador, you can see in the morning what went wrong with your machine’s routines. On Monday, you get a plain English summary of what’s worth fixing, and you decide.

## 📖 Guide

To understand what it does and how it changes your day (without the technical details): **https://inematds.github.io/zelador/guia/en/**

## What it is

People who leave robots and AI agents working on their own only find out there’s a problem when someone complains. Zelador is a free program that keeps an eye on things for you: every night, it checks what failed, and every week it gathers what’s worth improving into a simple form for you to decide. If you don’t already track failures and pending tasks, it creates the files. If you do, it uses yours. To install it, just ask your AI.

## What it sees and what it doesn’t

- **Sees:** scheduled routines on the computer itself or a Linux server that log errors, low memory, repeated errors, nearly full disks, and anything you or your AI record in the failure, limits, and pending task lists.
- **Doesn’t see:** what runs on internet services; system, administrator, or other account routines; cron tasks without a log file; routines that stop running without logging an error; routines that log an error but finish as if they succeeded; or incorrect results that finish without an error (unless the failure is recorded).
- **When nobody is logged in** (a server, or a computer that restarted): account schedules only run with `sudo loginctl enable-linger <usuário>`. The diagnosis warns you if this is missing.
- **If no message arrives in the morning, be suspicious:** by default, it sends a line even after a quiet night, so silence means the round may not have run.
- **Sensitive data:** alerts and reports may include excerpts from logs, and the AI explanation sends the title, proposal, and evidence. If logs contain customer data, set `noite.trechos = false` and leave `explicar.comando` empty.
- Cron tasks are only visible through what appears in the log file: use `>> arquivo.log 2>&1`.
- If it can’t inspect part of the system, the alert says which part instead of saying the night was quiet.
- Alerts are sent only after you choose a channel. The form opens on the computer where Zelador is running; to open it on your phone, connect both devices to a private network and set the address in `painel.enderecos` and `painel.link`.
- Tested on Linux. Mac and Windows have not been tested yet.

## How to get started (no technical skills needed)

Open Claude Code or Codex on the machine where the routines run, in the folder where your projects are stored, and paste:

```text
Read the Zelador project at https://github.com/inematds/zelador (the README explains everything, including installation).
Download a copy to a temporary folder outside my projects, and run only the diagnosis from the folder where my projects are stored (look for it if I don’t know where it is). Don’t change anything.
Then answer me in plain English:
1. Can it see the routines running here? What would it see, what wouldn’t it see, and will it keep running when nobody is logged in?
2. What do I already have that it can use?
3. What’s missing that it would create?
4. Where would I receive alerts, and what would I need to do for that?
Don’t install or change anything yet. Show me the plan and wait for me to say yes.
When I say yes, install it in a permanent folder, never the temporary one.
```

---

## Technical installation

Python 3.11+, standard library only. Tested on Linux; sources that don’t exist on the machine (no `journalctl`, no cron) are skipped and listed as skipped in the report. No API: the optional AI explanation uses the command you choose (for example, `claude -p` with your subscription).

```bash
git clone https://github.com/inematds/zelador.git && cd zelador
python3 -m unittest discover -s tests -v     # 21 testes, sem rede
bin/zelador iniciar                          # diagnóstico: não escreve nada
bin/zelador iniciar --aplicar                # cria o que falta, nunca sobrescreve
bin/zelador bloco                            # instrução para colar no CLAUDE.md/AGENTS.md
bin/zelador agendar --aplicar                # (clone numa pasta permanente) madrugada 04:20, pauta segunda 07:45, painel sempre ligado
```

The diagnosis answers item by item:

| Output | Meaning |
|---|---|
| `✓ JÁ TEM` | Zelador uses it as is |
| `→ PROPOSTA` | You have something similar or can connect a source; it explains and you decide |
| `+ CRIAR` | Nothing exists; with `--aplicar` it creates one from the template |

A similar name (`ERRORS.md`, `TODO.md`) is adopted by `--aplicar` only when you don’t already have a file of that type. If you do, it stays a suggestion.

## The process, from start to finish

🧠 you · ⚙️ script/timer · 🤖 AI (optional)

| # | Step | Command | Who |
|---|---|---|---|
| 1 | See what you already have and what’s missing | `zelador iniciar` | 🧠 |
| 2 | Create what’s missing and map what you already use | `zelador iniciar --aplicar` | ⚙️ |
| 3 | Tell the agent to record failures, limits, and pending tasks (paste into CLAUDE.md/AGENTS.md) | `zelador bloco` | 🧠 |
| 4 | Choose the alert channel (Telegram, desktop, or none) and, if you want, the AI that explains | edit `~/.config/zelador/zelador.toml` | 🧠 |
| 5 | Schedule | `zelador agendar --aplicar` | ⚙️ |
| 6 | Every day at 04:20: routine failures, low memory, repeated errors, cron errors, new logs, disk | `zelador noite` | ⚙️ |
| 7 | Every Monday at 07:45: agenda of recurring failures, serious overnight issues, your other monitors, open limits, and stalled pending tasks | `zelador pauta --avisar` | ⚙️ |
| 8 | Each new item gets a plain English explanation: what happened, why it matters, what the proposal does | `explicar.comando` | 🤖 |
| 9 | Read and decide in the dashboard: Approve, Reject (hidden for 8 weeks), Review, Postpone, with a note | `zelador painel` → http://127.0.0.1:8810/ | 🧠 |
| 10 | Wrap up the week: approved and “review” items go into pending tasks, and the alert sends the scorecard | button in the dashboard | 🧠 |

## Where everything lives

- Configuration: `~/.config/zelador/zelador.toml` (commented example in `exemplos/zelador.toml`).
- Data: `~/.local/share/zelador/` — `noite/` (overnight reports), `pautas/`, `decisoes.json`, `explicacoes.json`.
- Templates for files it creates: `zelador/modelos/`.
- Telegram alerts: `zelador/modelos/avisar-telegram.sh` (token in one of your own files, never in the repository).
- Demo agenda with invented data: `exemplos/pauta-demo.json`.

## Security

- Diagnosis only reads. `--aplicar` creates files that don’t exist and saves the previous config as `.toml.antes`.
- It never edits your CLAUDE.md/AGENTS.md: it shows you the block to paste.
- The dashboard listens only on `127.0.0.1`; another address (VPN) is available only if you set it in `painel.enderecos`.
- `tests/test_sem_dados_sensiveis.py` rejects versioned home paths, IPs, email addresses, tokens, and personal configuration or data.

## License

MIT.