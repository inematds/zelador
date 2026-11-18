# Falhas

| data | o que quebrou | menor correção | prompt \| infra |
|---|---|---|---|
| 2026-11-18 | aviso dizia "noite limpa" sem ter conseguido olhar journal, cron ou registros do sistema | listar no aviso o que não foi verificado e nunca dizer "limpa" nesse caso | infra |
| 2026-11-18 | erro do cron sumia do aviso quando havia item grave; erro em português, `$HOME` e log relativo não eram lidos | cron sempre no aviso, padrões em português, resolver caminho e contar log ausente como não verificado | infra |
| 2026-11-18 | guia e roteiro diziam "primeira noite", mas a medição foi uma rodada manual às 23h24 | trocar por "primeira rodada" e dizer que olhou as 24 horas anteriores | prompt |
| 2026-11-18 | banners antigos foram relançados porque o ajuste do script falhou antes de gravar | conferir o script alterado antes de disparar geração em segundo plano | prompt |
