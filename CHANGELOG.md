# Changelog

## 1.2.2 — 2026-11-18

- A explicação por IA passa a trazer causa provável e conserto sugerido, lendo o fim do registro da rotina (senhas ocultadas; `explicar.ler_registros`).
- Rotina parada é apontada na primeira execução perdida: o ritmo vem do histórico da máquina.
- O relatório diário traz o endereço do formulário.

## 1.1.2 — 2026-11-18

- Detecta rotina que parou de rodar: aprende o ritmo de cada timer ativo, noite após noite.
- Detecta rotina que terminou bem mas escreveu erro na saída ou no arquivo próprio.
- Tarefa do cron sem atividade muito além do previsto vira ponto de atenção.

## 1.0.2 — 2026-11-18

- A madrugada nunca diz "limpa" sobre o que não conseguiu olhar: o aviso lista o que não foi verificado.
- Tarefa do cron sem arquivo de registro aparece como não verificada; o diagnóstico avisa sobre ela, sobre o alcance da conta e sobre o linger em servidor.
- Logs do cron: reconhece erro em português, resolve `$HOME` e conta log inexistente como não verificado; erro do cron aparece no aviso mesmo com itens graves e entra na pauta.
- Frases como "sem erro" não contam como erro; a primeira leitura de um log é marcada; o aviso sai em linguagem mais simples e sugere colar na IA.
- `noite.trechos = false` tira trechos dos registros do aviso e do relatório; mais padrões de erro reconhecidos.
- Journal sem nenhuma linha conta como não verificado. Textos do aviso e das propostas mais simples.

## 1.0.0 — 2026-11-17

- `zelador iniciar`: diagnóstico (já tem / proposta / criar) e `--aplicar` que cria o que falta sem sobrescrever
  e mapeia os nomes que a pessoa já usa quando ela ainda não tem o padrão.
- `zelador noite`: falhas de rotina, OOM, erro repetido, erros novos nos logs do cron, registros novos, disco.
- `zelador pauta`: falhas que voltam (motor interno ou agente-que-aprende), madrugadas, relatórios de outros
  monitores, grupos de projetos, limites abertos, pendências paradas; explicação simples opcional por comando externo.
- `zelador painel`: formulário aprovar/recusar/analisar/adiar com nota; "Fechar a semana" grava nas pendências.
- `zelador agendar`: timers do systemd do usuário ou linhas de cron.
- Id do item ancorado no registro mais antigo: não muda quando o erro volta.
