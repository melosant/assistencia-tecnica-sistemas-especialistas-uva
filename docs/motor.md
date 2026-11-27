# Motor de inferência

Arquivo: `sistema_especialista/inferencia.py`. Usa as fórmulas de `sistema_especialista/incerteza.py`.

## Tipo de encadeamento

**Encadeamento para frente** (*forward chaining*, guiado pelos dados). O motor parte dos fatos informados na triagem e aplica as regras até não haver mais o que concluir. Ele não parte de uma hipótese para tentar prová-la, como no encadeamento para trás.

Por que para frente: na triagem, todas as perguntas são feitas antes e o objetivo é descobrir **tudo** o que os sinais indicam (quadros, cor, encaminhamento e avisos), não confirmar uma única hipótese.

## Memória de trabalho

É um dicionário `fato → certeza` (`ResultadoInferencia.memoria`). Um fato é sempre um texto `atributo=valor`:

- **fatos de entrada** são as respostas da triagem, como `sinais_avc=sim` e `febre=moderada`;
- **fatos derivados** são as conclusões do motor, como `quadro=suspeita_avc` e `classificacao=vermelho`. Os atributos derivados são `quadro`, `classificacao`, `encaminhamento` e `aviso` (`kb/fatos.json → derivados`).

No início, a memória recebe as respostas com certeza 1,0. As respostas "não sei" entram com a certeza informada em `cf_entradas` (0,5, valor de `config.cf_resposta_nao_sei`).

## As três camadas

As 20 regras estão divididas em camadas, e uma camada só usa fatos produzidos por camadas anteriores (o carregador da base valida isso):

```
respostas ──► Camada 1 (R01–R12) ──► quadro ──► Camada 2 (R13–R17) ──► classificacao ──► Camada 3 (R18–R20) ──► encaminhamento
                      └─► aviso (R06, R07)                                                         └─► aviso (R18)
```

Como cada camada roda uma vez, em ordem, **cada regra dispara no máximo uma vez** e não há laço infinito. Uma consulta completa forma cadeias de 3 passos, por exemplo: `sinais_avc=sim` → R05 → `quadro=suspeita_avc` → R13 → `classificacao=vermelho` → R18 → `encaminhamento=sala_de_emergencia`.

## Fluxo de uma consulta

1. `terminal.coletar_entradas` faz as perguntas e devolve `respostas` (`{"sinais_avc": "sim", ...}`) e `cf_entradas` (só as respostas com certeza menor que 1).
2. `inferir(base, respostas, cf_entradas)` monta a memória (`_montar_memoria`).
3. Para cada camada, em ordem crescente, e para cada regra da camada, na ordem do arquivo:
   1. **Casamento** (`_avaliar_se`): cada condição precisa ter na memória pelo menos um dos seus valores com certeza > 0. Numa condição com `|` (OU, como `febre=moderada|alta`), vale o valor presente com maior certeza. Se alguma condição falha, a regra não dispara.
   2. **Certeza do SE:** a menor certeza entre as condições (`cf_condicao`).
   3. **Certeza de cada conclusão:** a certeza do SE vezes a certeza da regra (`cf_conclusao`).
   4. **Atualização da memória:** se o fato ainda não existe, ele entra com essa certeza. Se já existe, porque outra regra o concluiu antes, as certezas são combinadas (`combinar`).
   5. **Registro:** um `Disparo` guarda a regra, a certeza do SE, os fatos usados e as conclusões geradas. O módulo de explicação usa esse registro.
4. **Filtro pelo limiar:** `conclusoes` recebe apenas os fatos **derivados** com certeza ≥ `limiar_cf` (0,4).
5. `classificacao_final` escolhe a cor (veja abaixo).
6. `terminal.exibir_resultado` mostra o resultado e, se o usuário pedir, o "como".

## Incerteza (fatores de certeza)

Um fator de certeza (cf) é um número de 0 a 1. São três fórmulas, em `incerteza.py`:

| Situação | Fórmula | Função | Ideia |
| --- | --- | --- | --- |
| Várias condições ligadas por E | `min(cf₁, cf₂, …)` | `cf_condicao` | a corrente arrebenta no elo mais fraco |
| Conclusão de uma regra | `cf_SE × cf_regra` | `cf_conclusao` | as incertezas se acumulam |
| Duas regras concluem o mesmo fato | `a + b × (1 − a)` | `combinar` | a segunda evidência preenche só a dúvida que sobrou; nunca passa de 1 |

As três funções lançam `ValueError` se recebem valor fora de [0, 1] ou uma lista vazia, o que denuncia erros de programação logo.

### Exemplo completo: idoso hipertenso com dor forte no peito

Respostas: `dor_toracica=tipica` (1,0), `grupo_risco=sim` (1,0) e o restante sem alerta.

| Passo | Regra | Cálculo | Resultado |
| --- | --- | --- | --- |
| 1 | R03 | 1,0 × 0,8 | `quadro=suspeita_cardiaca` = 0,80 |
| 2 | R04 | min(1,0; 1,0) × 0,6 = 0,6, combinado com 0,8: 0,8 + 0,6 × 0,2 | `quadro=suspeita_cardiaca` = **0,92** |
| 3 | R13 | 0,92 × 0,95 | `classificacao=vermelho` = 0,874 |
| 4 | R18 | 0,874 × 0,95 | `encaminhamento=sala_de_emergencia` = 0,83 e `aviso=acionar_equipe_emergencia` = 0,83 |

### Exemplo com "não sei": sinais de AVC

Se a resposta para `sinais_avc` é "não sei", ela entra como `sinais_avc=sim` com 0,5:

- R05: 0,5 × 0,9 = 0,45, então `quadro=suspeita_avc` = 0,45 (passa do limiar de 0,4)
- R13: 0,45 × 0,95 = 0,4275, então `classificacao=vermelho`
- R18: 0,4275 × 0,95 ≈ 0,406, então o paciente vai para a sala de emergência

A cadeia inteira ainda passa do limiar: num sinal grave, a dúvida não impede o alerta.

## Resolução de conflito

Várias cores podem passar do limiar ao mesmo tempo. Por exemplo, um paciente com dor típica no peito **e** febre moderada em grupo de risco recebe `classificacao=vermelho` (0,87) e `classificacao=amarelo` (0,60).

**Vale a mais urgente, não a de maior certeza.** `classificacao_final` percorre `catalogo.json → ordem_urgencia` (`vermelho`, `laranja`, `amarelo`, `verde`) e devolve a primeira cor que está em `conclusoes`. Na dúvida, o paciente sobe de nível e nunca desce. O terminal mostra as outras cores numa linha de "Observação (resolução de conflito)".

Entre regras **não há conflito de disparo**: todas as regras cujo SE é satisfeito disparam, na ordem de camada e depois na ordem do arquivo, e conclusões repetidas se combinam.

## Casos de exceção

| Caso | Comportamento |
| --- | --- |
| Nenhum sinal de alerta (tudo "não") | Nenhuma regra dispara e `conclusoes` fica vazio. O terminal mostra "Não foi possível concluir com as informações fornecidas". |
| Há quadro, mas nenhuma cor passa do limiar | Exemplo: febre moderada e "não sei" no grupo de risco. R16 dá amarelo com 0,8 × 0,5 × 0,75 = 0,375, abaixo de 0,4. O terminal mostra os quadros e "Classificação de risco: inconclusiva". |
| Conclusão abaixo do limiar | Fica na memória, e regras das camadas seguintes ainda podem usá-la, mas o resultado delas sai com certeza ainda menor e também não é exibido. |
| Pergunta pulada ("não sei" e depois "0") | O atributo não entra na memória, e as regras que dependem dele não disparam. |
| Conflito de encaminhamento | Com duas cores, cada uma dispara a sua regra da camada 3. Os dois encaminhamentos aparecem, ordenados por certeza, e o da cor mais urgente vem primeiro. |
| Base de conhecimento inconsistente | `carregar` lança `BaseInvalida` com a lista de problemas. `main.py` mostra a mensagem e encerra com código 1. |
| Ctrl+C ou fim de entrada durante a consulta | A consulta é interrompida e o programa volta ao menu. No menu, o programa encerra. |
