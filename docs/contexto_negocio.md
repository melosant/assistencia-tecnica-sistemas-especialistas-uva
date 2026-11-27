# Contexto de negócio

## Empresa

**Clínica Vida Plena — Pronto Atendimento** (fictícia).

Segmento: prestação de serviços de saúde, no pronto atendimento de uma clínica que faz a triagem de pacientes adultos.

## Problema

Nos horários de pico, a triagem feita pela recepção de enfermagem varia conforme o profissional. Pacientes graves podem ficar esperando enquanto casos leves são atendidos antes. Falta um critério único, que todos apliquem do mesmo jeito.

## Solução proposta

Um **sistema especialista** de apoio à triagem. O profissional responde no terminal até 9 perguntas objetivas sobre o paciente (consciência, respiração, dor no peito, sinais de AVC, sangramento, febre, dor abdominal, trauma e grupo de risco). O sistema então:

1. **classifica o risco por cores**, com o tempo máximo de espera de cada uma:

   | Cor | Nome | Tempo máximo de espera |
   | --- | --- | --- |
   | Vermelho | Emergência | imediato |
   | Laranja | Muito urgente | 10 min |
   | Amarelo | Urgente | 60 min |
   | Verde | Pouco urgente | 120 min |

2. **indica o encaminhamento**: sala de emergência, consultório com prioridade ou fila ambulatorial;
3. **emite avisos imediatos à equipe**: acionar a equipe de emergência, comprimir o sangramento, imobilizar o paciente;
4. **explica o raciocínio**: mostra quais regras levaram a cada conclusão (o "como") e por que cada pergunta é feita (o "por quê");
5. **informa a certeza** de cada conclusão em porcentagem e aceita a resposta "não sei".

## Por que um sistema especialista

- O conhecimento da triagem cabe em regras do tipo SE/ENTÃO, que um enfermeiro consegue ler e revisar.
- As regras ficam em arquivos JSON (`kb/`), separadas do código: dá para mudar o protocolo sem programar.
- Toda conclusão vem com a cadeia de regras que a sustenta, o que é necessário num contexto em que a decisão precisa ser justificada.
- Na dúvida, o sistema **sobe** o nível de urgência, nunca desce (veja [motor.md](motor.md#resolução-de-conflito)).

## Usuário

O profissional de triagem (enfermagem ou recepção treinada). O paciente não usa o sistema diretamente.

## Aviso legal

> Protocolo simplificado e fictício, criado para fins acadêmicos. É uma ferramenta de apoio à triagem e não substitui a avaliação de um profissional de saúde. Em caso de dúvida, o sistema sempre privilegia o nível de maior urgência.

Esse aviso aparece no cabeçalho do programa sempre que ele é aberto. Os textos e tempos estão em `kb/fatos.json` e `kb/catalogo.json`.
