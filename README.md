# 🔦 Zelador

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

[![Zelador](guia/assets/banner.jpg)](https://inematds.github.io/zelador/guia/)

**O agente Zelador te ajuda a melhorar o seu sistema todo dia.** Sem ele, você só descobre o problema quando alguém reclama. Com ele, as rotinas da sua máquina são conferidas toda madrugada e, de manhã, ele te avisa. Se você ligar a explicação pela sua IA, ele investiga a causa e sugere o conserto. Você decide e pede à IA para fazer.

## 📖 Guia

Para entender o que ele faz e como muda o seu dia (sem parte técnica): **https://inematds.github.io/zelador/guia/**

## O que é

Quem deixa robôs e agentes de IA trabalhando sozinhos só descobre o problema quando alguém reclama. O Zelador é um programa gratuito que fica de olho nisso por você: toda madrugada ele confere o que falhou, e toda semana junta o que vale melhorar num formulário simples, para você decidir. Se você ainda não anota falhas e pendências, ele cria os arquivos. Se já anota, ele usa os seus. Para instalar, basta pedir à sua IA.

## O que ele vê e o que não vê

- **Vê:** rotinas agendadas no próprio computador ou servidor Linux que falham, escrevem erro ou param de rodar (o ritmo de cada uma vem do histórico da máquina), falta de memória, erros repetidos, disco quase cheio e tudo o que você ou a sua IA anotam nas listas de falhas, limites e pendências.
- **Não vê:** o que roda em serviços na internet, rotinas do sistema, do administrador ou de outra conta, tarefa do cron sem arquivo de registro, e resultado errado que não deixa nenhum sinal (a não ser que a falha seja anotada).
- **Sem ninguém conectado** (servidor, ou computador que reiniciou): os agendamentos da conta só rodam com `sudo loginctl enable-linger <usuário>`. O diagnóstico avisa quando falta.
- **Se nenhuma mensagem chegar de manhã, desconfie:** por padrão ele manda uma linha mesmo em noite limpa, então o silêncio indica que a ronda pode não ter rodado.
- **Dados sensíveis:** o aviso e o relatório podem levar trechos dos registros, e a explicação por IA envia título, proposta e evidências. Se os registros têm dados de clientes, use `noite.trechos = false` e deixe `explicar.comando` vazio.
- Tarefa do cron só é vista pelo que aparece no arquivo de registro: use `>> arquivo.log 2>&1`.
- Se não conseguir olhar alguma parte, o aviso diz qual, em vez de dizer que a noite foi limpa.
- O aviso só sai depois que você escolhe o canal. O formulário abre no computador onde o Zelador está, e o endereço aparece em todo relatório da madrugada; para abrir no celular, ligue os dois por uma rede privada e ponha o endereço em `painel.enderecos` e `painel.link`.
- Testado em Linux. Mac e Windows ainda não foram testados.

## Como começar (sem ser técnico)

Abra o Claude Code, ou o Codex, na máquina onde as rotinas rodam, na pasta onde ficam os seus projetos, e cole:

```text
Leia o projeto Zelador em https://github.com/inematds/zelador (o README explica tudo, inclusive a instalação).
Baixe uma cópia numa pasta temporária, fora dos meus projetos, e rode só o diagnóstico, a partir da pasta onde ficam os meus projetos (procure; se eu não tiver, siga sem ela). Não altere nada.
Depois me responda em português simples:
1. Ele enxerga as rotinas que rodam aqui? O que ele veria, o que não veria, e ele continua rodando sem ninguém conectado?
2. O que eu já tenho e ele pode aproveitar?
3. O que falta e ele criaria?
4. Por onde eu receberia os avisos, e o que eu precisaria fazer para isso?
Não instale nem mude nada ainda. Mostre o plano e espere eu dizer sim.
Quando eu disser sim, instale numa pasta permanente, nunca na temporária.
```

---

## Instalação técnica

Python 3.11+, só biblioteca padrão. Testado em Linux; fonte que não existe na máquina (sem `journalctl`, sem cron) é pulada e aparece no relatório como pulada. Sem API: a explicação por IA é opcional e usa o comando que você escolher (por exemplo `claude -p` pela assinatura).

```bash
git clone https://github.com/inematds/zelador.git && cd zelador
python3 -m unittest discover -s tests -v     # 27 testes, sem rede
bin/zelador iniciar                          # diagnóstico: não escreve nada
bin/zelador iniciar --aplicar                # cria o que falta, nunca sobrescreve
bin/zelador bloco                            # instrução para colar no CLAUDE.md/AGENTS.md
bin/zelador agendar --aplicar                # (clone numa pasta permanente) madrugada 04:20, pauta segunda 07:45, painel sempre ligado
```

O diagnóstico responde peça por peça:

| Saída | Quer dizer |
|---|---|
| `✓ JÁ TEM` | o zelador usa como está |
| `→ PROPOSTA` | você tem algo parecido ou pode ligar uma fonte; ele explica e você decide |
| `+ CRIAR` | não existe nada; com `--aplicar` ele cria a partir do modelo |

Um nome parecido (`ERRORS.md`, `TODO.md`) só é adotado por `--aplicar` quando você ainda não tem nenhum arquivo daquele tipo. Se já tem, fica como sugestão.

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
| 8 | Cada item novo ganha a explicação simples, a causa provável e o conserto sugerido, lendo o fim dos registros da rotina e dos logs recentes do projeto, tentando ocultar senhas, sem garantia (`explicar.ler_registros`) | `explicar.comando` | 🤖 |
| 9 | Ler e decidir no painel: Aprovar, Recusar (some por 8 semanas), Analisar, Adiar, com nota | `zelador painel` → http://127.0.0.1:8810/ | 🧠 |
| 10 | Fechar a semana: aprovadas e "analisar" entram nas pendências, e o aviso manda o placar | botão no painel | 🧠 |

## Onde fica cada coisa

- Configuração: `~/.config/zelador/zelador.toml` (exemplo comentado em `exemplos/zelador.toml`).
- Dados: `~/.local/share/zelador/` — `noite/` (relatórios da madrugada), `pautas/`, `decisoes.json`, `explicacoes.json`.
- Modelos dos arquivos que ele cria: `zelador/modelos/`.
- Aviso pelo Telegram: `zelador/modelos/avisar-telegram.sh` (token num arquivo seu, nunca no repositório).
- Pauta de demonstração, com dados inventados: `exemplos/pauta-demo.json`.

## Segurança

- O diagnóstico só lê. `--aplicar` cria arquivos que não existem e guarda a config anterior em `.toml.antes`.
- Nunca edita seu CLAUDE.md/AGENTS.md: mostra o bloco para você colar.
- O painel escuta só em `127.0.0.1`; outro endereço (VPN) só se você puser em `painel.enderecos`.
- `tests/test_sem_dados_sensiveis.py` reprova caminho de casa, IP, e-mail, token e config ou dados pessoais versionados.

## Licença

MIT.
