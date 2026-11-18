# Changelog

## 1.0.0 — 2026-11-17

- `zelador iniciar`: diagnóstico (já tem / proposta / criar) e `--aplicar` que cria o que falta sem sobrescrever
  e mapeia os nomes que a pessoa já usa quando ela ainda não tem o padrão.
- `zelador noite`: falhas de rotina, OOM, erro repetido, erros novos nos logs do cron, registros novos, disco.
- `zelador pauta`: falhas que voltam (motor interno ou agente-que-aprende), madrugadas, relatórios de outros
  monitores, grupos de projetos, limites abertos, pendências paradas; explicação simples opcional por comando externo.
- `zelador painel`: formulário aprovar/recusar/analisar/adiar com nota; "Fechar a semana" grava nas pendências.
- `zelador agendar`: timers do systemd do usuário ou linhas de cron.
- Id do item ancorado no registro mais antigo: não muda quando o erro volta.
