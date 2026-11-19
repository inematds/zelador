# Ideias a incorporar no zelador

Anotado em 19/11/2026, a pedido do Nei. São práticas que já usamos para não perder o trabalho das sessões.
Ainda não estão no código; entram depois como verificações do diagnóstico ou como itens da config.
Os caminhos reais desta máquina ficam em `LOCAL-NESTA-MAQUINA.md`, que não é versionado.

## 1. Não perder o projeto que está sendo feito

- **Toda sessão de terminal fica registrada.** Ao abrir uma sessão do agente, um gancho grava quem é
  (projeto, pid, tty, pasta, hora), e ao fechar apaga o registro. Se o processo morrer sem fechar,
  o registro vai para uma lista de "sessões interrompidas". Assim dá para saber o que caiu no meio.
- **Handoff gravado durante o trabalho.** Nas faixas de contexto (~50%, ~70%, ~85%) e depois de cada
  compactação, o agente grava um handoff: um retrato do estado atual, com o que falta e as ordens dadas,
  que nunca sobrescreve o anterior. Um índice aponta o mais recente e o que está aberto por assunto.
- **Handoff de novo antes de o cache vencer.** Se a sessão fica parada perto do fim do cache (1 h),
  o handoff é salvo outra vez, para a próxima sessão retomar lendo só o arquivo (`/prime`).
- **Conferência.** Um gancho confere se o handoff foi mesmo gravado depois do pedido e avisa quando não foi.
- **Espera longa.** Quando o trabalho fica esperando (render, avatar), a sessão escreve um bilhete
  `CONTINUAR.md` e um vigia abre uma sessão nova quando estiver pronto.

- **Vigias para não perder o terminal.** Rotinas de poucos em poucos minutos que olham o que ficou para trás:
  o vigia de continuação (a cada 5 min) abre a sessão nova quando a espera termina; o vigia de execução
  longa (a cada 10 min) avisa quando uma execução parou por estagnação ou teto, quando o laço morreu sem
  aviso, ou quando a sessão ficou ociosa (nada mudou há mais de 30 min). Cada problema avisa uma vez.
- **Laço para sessões grandes.** Trabalho de horas roda num laço externo sem tela: cada ciclo é uma chamada
  nova do agente com teto de tempo e memória. Quem decide se continua é o teste, não o agente; testes
  protegidos voltam ao original se o agente mexer; para depois de 3 ciclos sem avanço. Cada execução tem
  pasta própria com objetivo, plano, estado, progresso, falhas, decisões e um canal só de acréscimo.

**O que o zelador pode checar:** sessões interrompidas sem handoff; execução longa parada ou ociosa;
rotinas de vigia desligadas; projeto com trabalho aberto e handoff
velho; bilhete de continuação parado há muito tempo.

## 2. Arquivos de registro do sistema

Arquivos que já mantemos e que o zelador pode ler (só leitura) para montar o relatório:

| Arquivo | O que guarda |
|---|---|
| FALHAS.md | uma linha por falha: data, o que quebrou, menor correção, prompt ou infra |
| LIMITES.md | o que a ferramenta, a cota ou o ambiente não deixou fazer, com contorno e status |
| LESSONS.md | lição de cada correção, uma linha, mais recente no topo |
| revisor-falhas.md | cada reprovação do revisor independente, com nota e detalhe |
| pendencias.md | o que ficou para "olhar depois", resolvidas no fim com data |
| GUIAS-SEM-VIDEO.md | guias que ainda não têm vídeo |
| handoffs/latest.md | trabalho aberto por assunto |

**O que o zelador pode checar:** falhas e limites com status `aberto` há muito tempo; reprovações que se
repetem; pendências antigas; mesma falha aparecendo em vários projetos.

## 3. Referências para ligar depois

- **EngineBridge** — escolhe qual motor de IA atende cada etapa e usa a alternativa declarada quando a
  cota acaba. Referência para o `explicar.comando` do zelador e para chamar outro motor quando um falhar.
- **Skill session-handoff** — grava o handoff (script `handoff-grava.py`) e mantém o índice.
- **Gancho de execução longa** — avisa as faixas de contexto, cobra e confere o handoff, bloqueia uma vez
  quando o cache venceu.
- **Painel de monitoramento** — painel web local com vagas da máquina, filas e sessões. O zelador pode
  mandar o resumo para lá em vez de só para o relatório.
