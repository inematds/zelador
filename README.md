# zelador

Toda madrugada ele olha se alguma rotina falhou, se faltou memória ou se um erro está se repetindo, e te avisa.
Toda segunda ele junta as propostas de melhoria da semana num formulário: você lê a explicação em português
simples e aprova, recusa, pede análise ou adia. O que você aprovou vira pendência.

Se você ainda não tem arquivo de falhas, de limites ou de pendências, ele cria. Se já tem algo com outro nome
(`ERRORS.md`, `TODO.md`…), ele usa o seu em vez de criar outro. Se você já tem monitores, ele propõe ler o
relatório deles em vez de duplicar.

Python 3.11+, só biblioteca padrão. Sem API: a explicação por IA é opcional e usa o comando que você escolher
(por exemplo `claude -p` pela assinatura).

## Começar

```bash
git clone https://github.com/inematds/zelador.git && cd zelador
python3 -m unittest discover -s tests -v     # 14 testes, sem rede
bin/zelador iniciar                          # diagnóstico: não escreve nada
bin/zelador iniciar --aplicar                # cria o que falta, nunca sobrescreve
bin/zelador agendar --aplicar                # madrugada 04:20, pauta segunda 07:45, painel sempre ligado
```

O diagnóstico responde peça por peça:

| Saída | Quer dizer |
|---|---|
| `✓ JÁ TEM` | o zelador usa como está |
| `→ PROPOSTA` | você tem algo parecido ou pode ligar uma fonte; ele explica e você decide |
| `+ CRIAR` | não existe nada; com `--aplicar` ele cria a partir do modelo |

## O processo, do início ao fim

🧠 você · ⚙️ script/timer · 🤖 IA (opcional)

| # | Passo | Comando | Quem |
|---|---|---|---|
| 1 | Ver o que você já tem e o que falta | `zelador iniciar` | 🧠 |
| 2 | Criar o que falta e mapear o que você já usa | `zelador iniciar --aplicar` | ⚙️ |
| 3 | Mandar o agente registrar falhas, limites e pendências (cole no CLAUDE.md/AGENTS.md) | `zelador bloco` | 🧠 |
| 4 | Escolher o aviso (Telegram, desktop ou nenhum) e, se quiser, a IA que explica | editar `~/.config/zelador/zelador.toml` | 🧠 |
| 5 | Agendar | `zelador agendar --aplicar` | ⚙️ |
| 6 | Todo dia 04:20: falhas de rotina, falta de memória, erro repetido, erros do cron, registros novos, disco | `zelador noite` | ⚙️ |
| 7 | Toda segunda 07:45: pauta com as falhas que voltam, madrugadas graves, seus outros monitores, limites abertos e pendências paradas | `zelador pauta --avisar` | ⚙️ |
| 8 | Cada item novo ganha a explicação simples: o que aconteceu, por que importa, o que a proposta faz | `explicar.comando` | 🤖 |
| 9 | Ler e decidir no painel: Aprovar, Recusar (some por 8 semanas), Analisar, Adiar, com nota | `zelador painel` → http://127.0.0.1:8810/ | 🧠 |
| 10 | Fechar a semana: aprovadas e "analisar" entram nas pendências, e o aviso manda o placar | botão no painel | 🧠 |

## Onde fica cada coisa

- Configuração: `~/.config/zelador/zelador.toml` (exemplo comentado em `exemplos/zelador.toml`).
- Dados: `~/.local/share/zelador/` — `noite/` (relatórios da madrugada), `pautas/`, `decisoes.json`, `explicacoes.json`.
- Modelos dos arquivos que ele cria: `zelador/modelos/`.
- Aviso pelo Telegram: `zelador/modelos/avisar-telegram.sh` (token num arquivo seu, nunca no repositório).

## Segurança

- O diagnóstico só lê. `--aplicar` cria arquivos que não existem e guarda a config anterior em `.toml.antes`.
- Nunca edita seu CLAUDE.md/AGENTS.md: mostra o bloco para você colar.
- O painel escuta só em `127.0.0.1`; outro endereço (VPN) só se você puser em `painel.enderecos`.
- Fonte que não existe na máquina (sem `journalctl`, sem cron) é pulada e aparece no relatório como pulada.

## Licença

MIT.
