## Registro de falhas, limites e pendências (zelador)

- **Falha:** ao terminar de corrigir qualquer falha real (travou, caiu, quebrou, gerou errado), escreva uma linha no
  `FALHAS.md` do projeto (ou no do hub, se a falha atravessa projetos): `| data | o que quebrou | menor correção | prompt \| infra |`.
  Antes de partir para a próxima tarefa, não no fim da sessão.
- **Limite:** quando uma ferramenta, permissão, cota ou ambiente te barrar, uma linha no `LIMITES.md`:
  `| data | o que tentei | o que barrou | contorno | proposta para destravar | aberto |`.
- **Pendência:** quando pedirem para "olhar depois", uma linha `- [ ] **data — assunto** detalhe` no topo do `PENDENCIAS.md`.
- O zelador lê esses arquivos toda madrugada e toda semana; as propostas aprovadas no painel voltam como pendências.
