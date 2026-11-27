# Dicionário de fatos e regras

> Gerado automaticamente por `scripts/gerar_dicionario.py` a partir de `kb/`. Não edite à mão.

## Configuração

- **Limiar de certeza (`limiar_cf`):** 0.4 — conclusões abaixo disso não são apresentadas.
- **Certeza da resposta "não sei" (`cf_resposta_nao_sei`):** 0.5

## Fatos de entrada (perguntas da triagem)

Cada resposta vira um fato `atributo=valor` com certeza 1,0 (ou a do "não sei").

| Atributo | Pergunta | Valor | Significado | Usado em |
| --- | --- | --- | --- | --- |
| `consciencia` | Como está o nível de consciência do paciente? | `alerta` | Alerta e responde normalmente | R01, R08 |
| | | `confuso` | Confuso ou muito sonolento | |
| | | `inconsciente` | Desmaiado ou não responde | |
| `respiracao` | Como está a respiração? | `normal` | Normal ou com falta de ar leve (consegue falar frases completas) | R02 |
| | | `falta_de_ar_intensa` | Falta de ar intensa (não consegue falar frases completas ou lábios arroxeados) | |
| `dor_toracica` | O paciente sente dor ou aperto no peito? | `nao` | Não | R03, R04, R11 |
| | | `leve` | Dor leve e localizada (pontada, piora ao tocar ou respirar) | |
| | | `tipica` | Aperto ou pressão forte, que pode ir para braço, mandíbula ou costas, com suor frio ou náusea | |
| `sinais_avc` | Há boca torta, fala arrastada ou fraqueza súbita em um lado do corpo? | `nao` | Não | R05 |
| | | `sim` | Sim | |
| `sangramento` | Há sangramento? | `nao` | Não, ou pequeno e controlado | R06 |
| | | `intenso` | Intenso (grande volume ou não para com compressão) | |
| `febre` | O paciente está com febre? | `nao` | Não | R08, R12 |
| | | `moderada` | Moderada (de 37,8 a 38,9 °C) | |
| | | `alta` | Alta (39 °C ou mais) | |
| `dor_abdominal` | O paciente sente dor na barriga? | `nao` | Não, ou dor leve | R09 |
| | | `intensa` | Dor intensa que não alivia | |
| `trauma` | Houve queda, pancada ou acidente? | `nenhum` | Não, ou lesão leve (pequeno corte, torção) | R07, R10 |
| | | `deformidade` | Suspeita de fratura (deformidade ou não consegue apoiar ou mexer o membro) | |
| | | `grave` | Acidente de trânsito, queda de altura ou pancada na cabeça com vômito ou desmaio | |
| `grupo_risco` | O paciente tem 60 anos ou mais, está grávida ou tem doença crônica (diabetes, hipertensão, doença do coração ou do pulmão)? | `sim` | Sim | R04, R16, R17 |
| | | `nao` | Não | |

## Fatos derivados (conclusões do motor)

| Fato | Descrição | Concluído por | Usado em |
| --- | --- | --- | --- |
| `quadro=rebaixamento_consciencia` | Rebaixamento do nível de consciência | R01 | R13 |
| `quadro=desconforto_respiratorio_grave` | Desconforto respiratório grave | R02 | R13 |
| `quadro=suspeita_cardiaca` | Suspeita de problema cardíaco agudo | R03, R04 | R13 |
| `quadro=suspeita_avc` | Suspeita de AVC | R05 | R13 |
| `quadro=hemorragia_grave` | Hemorragia grave | R06 | R13 |
| `quadro=trauma_grave` | Trauma grave | R07 | R14 |
| `quadro=febre_com_alteracao` | Febre alta com alteração de consciência | R08 | R14 |
| `quadro=dor_abdominal_intensa` | Dor abdominal intensa | R09 | R14 |
| `quadro=suspeita_fratura` | Suspeita de fratura | R10 | R15 |
| `quadro=dor_toracica_inespecifica` | Dor torácica leve a esclarecer | R11 | R15 |
| `quadro=sindrome_febril` | Síndrome febril | R12 | R16, R17 |
| `classificacao=vermelho` | Vermelho: emergência, atendimento imediato | R13 | R18 |
| `classificacao=laranja` | Laranja: muito urgente, atendimento em até 10 minutos | R14 | R19 |
| `classificacao=amarelo` | Amarelo: urgente, atendimento em até 60 minutos | R15, R16 | R19 |
| `classificacao=verde` | Verde: pouco urgente, atendimento em até 120 minutos | R17 | R20 |
| `encaminhamento=sala_de_emergencia` | Encaminhar direto para a sala de emergência | R18 | — |
| `encaminhamento=consultorio_prioritario` | Encaminhar ao consultório médico com prioridade sobre a fila comum | R19 | — |
| `encaminhamento=consulta_ambulatorial` | Encaminhar à fila normal de consulta ambulatorial | R20 | — |
| `aviso=acionar_equipe_emergencia` | Acionar a equipe de emergência imediatamente | R18 | — |
| `aviso=comprimir_sangramento` | Iniciar compressão direta do local do sangramento | R06 | — |
| `aviso=imobilizar_paciente` | Manter o paciente imobilizado até a avaliação médica | R07 | — |

## Classificações de risco

Ordem de urgência (da mais para a menos urgente): `vermelho` > `laranja` > `amarelo` > `verde`.

| Cor | Nome | Tempo máximo de espera |
| --- | --- | --- |
| vermelho | Emergência | imediato |
| laranja | Muito urgente | 10 min |
| amarelo | Urgente | 60 min |
| verde | Pouco urgente | 120 min |

## Regras (20)

### Camada 1 — Sinais → Quadro de triagem

| ID | SE (todas as condições) | ENTÃO (certeza da regra) | Justificativa |
| --- | --- | --- | --- |
| R01 | `consciencia=inconsciente` | `quadro=rebaixamento_consciencia` (0.95) | Paciente desmaiado ou que não responde tem a consciência comprometida, o que é sempre um sinal de gravidade. |
| R02 | `respiracao=falta_de_ar_intensa` | `quadro=desconforto_respiratorio_grave` (0.9) | Falta de ar que impede de falar frases completas ou deixa os lábios arroxeados indica troca de oxigênio comprometida. |
| R03 | `dor_toracica=tipica` | `quadro=suspeita_cardiaca` (0.8) | Aperto forte no peito, que irradia para braço ou mandíbula com suor frio ou náusea, é o padrão clássico de problema cardíaco agudo. |
| R04 | `dor_toracica=tipica` E `grupo_risco=sim` | `quadro=suspeita_cardiaca` (0.6) | Idade avançada ou doença crônica aumentam a chance de que a dor típica no peito seja de origem cardíaca. |
| R05 | `sinais_avc=sim` | `quadro=suspeita_avc` (0.9) | Boca torta, fala arrastada e fraqueza súbita de um lado são os sinais clássicos de AVC, em que cada minuto conta. |
| R06 | `sangramento=intenso` | `quadro=hemorragia_grave` (0.9)<br>`aviso=comprimir_sangramento` (0.9) | Sangramento de grande volume ou que não para com compressão pode levar a choque; a compressão local deve começar imediatamente. |
| R07 | `trauma=grave` | `quadro=trauma_grave` (0.85)<br>`aviso=imobilizar_paciente` (0.85) | Acidente de trânsito, queda de altura ou pancada na cabeça com vômito ou desmaio podem causar lesões internas ou na coluna; o paciente deve ser imobilizado. |
| R08 | `febre=alta` E `consciencia=confuso` | `quadro=febre_com_alteracao` (0.8) | Febre alta com confusão mental pode indicar infecção grave que afeta o sistema nervoso ou o organismo todo. |
| R09 | `dor_abdominal=intensa` | `quadro=dor_abdominal_intensa` (0.75) | Dor intensa na barriga que não alivia pode indicar problema que exige avaliação médica rápida. |
| R10 | `trauma=deformidade` | `quadro=suspeita_fratura` (0.8) | Deformidade ou incapacidade de apoiar ou mexer o membro após uma queda sugere fratura. |
| R11 | `dor_toracica=leve` | `quadro=dor_toracica_inespecifica` (0.7) | Mesmo uma dor leve no peito não pode ser descartada sem avaliação médica. |
| R12 | `febre=moderada\|alta` | `quadro=sindrome_febril` (0.8) | Febre de 37,8 °C ou mais indica um processo infeccioso ou inflamatório em curso. |

### Camada 2 — Quadro → Classificação de risco

| ID | SE (todas as condições) | ENTÃO (certeza da regra) | Justificativa |
| --- | --- | --- | --- |
| R13 | `quadro=rebaixamento_consciencia\|desconforto_respiratorio_grave\|suspeita_cardiaca\|suspeita_avc\|hemorragia_grave` | `classificacao=vermelho` (0.95) | Estes quadros ameaçam a vida em minutos; exigem atendimento imediato. |
| R14 | `quadro=trauma_grave\|febre_com_alteracao\|dor_abdominal_intensa` | `classificacao=laranja` (0.85) | Quadros muito urgentes, com risco de piorar rápido; o paciente deve ser visto em poucos minutos. |
| R15 | `quadro=suspeita_fratura\|dor_toracica_inespecifica` | `classificacao=amarelo` (0.8) | Casos urgentes, sem risco imediato à vida, mas que não devem esperar na fila comum. |
| R16 | `quadro=sindrome_febril` E `grupo_risco=sim` | `classificacao=amarelo` (0.75) | Idosos, gestantes e pessoas com doença crônica pioram mais rápido com infecção; a febre sobe a prioridade. |
| R17 | `quadro=sindrome_febril` E `grupo_risco=nao` | `classificacao=verde` (0.8) | Febre moderada em adulto sem fator de risco e sem sinais de alerta é pouco urgente. |

### Camada 3 — Classificação → Encaminhamento e avisos

| ID | SE (todas as condições) | ENTÃO (certeza da regra) | Justificativa |
| --- | --- | --- | --- |
| R18 | `classificacao=vermelho` | `encaminhamento=sala_de_emergencia` (0.95)<br>`aviso=acionar_equipe_emergencia` (0.95) | Emergência: o paciente vai direto para a sala de emergência e a equipe deve ser acionada na hora, sem passar por fila. |
| R19 | `classificacao=laranja\|amarelo` | `encaminhamento=consultorio_prioritario` (0.9) | Casos muito urgentes e urgentes passam na frente dos demais para o consultório médico, dentro do tempo máximo da cor. |
| R20 | `classificacao=verde` | `encaminhamento=consulta_ambulatorial` (0.9) | Caso pouco urgente segue a fila normal de consulta ambulatorial. |
