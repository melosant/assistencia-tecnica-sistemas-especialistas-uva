# Arquitetura e módulos

Este documento explica como o sistema funciona de ponta a ponta e o que faz cada arquivo. Os detalhes do raciocínio (encadeamento, certeza, conflitos) estão em [motor.md](motor.md). O conteúdo das 20 regras está em [dicionario_regras.md](dicionario_regras.md), e o problema de negócio em [contexto_negocio.md](contexto_negocio.md).

## Visão geral

Um sistema especialista tem três partes clássicas, e cada uma é um módulo separado:

| Parte clássica | Onde está no projeto |
| --- | --- |
| Base de conhecimento (fatos e regras) | `kb/*.json`, lida por `base_conhecimento.py` |
| Motor de inferência | `inferencia.py`, com as fórmulas de `incerteza.py` |
| Interface com o usuário e explicação | `terminal.py` e `explicacao.py` |

```
            kb/fatos.json   kb/regras.json   kb/catalogo.json
                     \             |              /
                      ▼            ▼             ▼
main.py ──► base_conhecimento.carregar() ──► BaseConhecimento (validada)
                                                   │
                                                   ▼
                                    terminal.iniciar(base)  ── menu
                                                   │
                      ┌────────────────────────────┼─────────────────────────────┐
                      ▼                            ▼                             ▼
          coletar_entradas()            inferencia.inferir()           exibir_resultado()
          perguntas, "não sei", "?"     encadeamento para frente        cor, tempo, quadros,
          (por quê → regras_que_usam)   + incerteza.py                  encaminhamento, avisos
                      │                            │                    + explicacao.explicar_como()
                      └── respostas, cf_entradas ──┘── ResultadoInferencia ──┘
```

O código **não contém conhecimento clínico**. Perguntas, regras, certezas, cores, tempos e textos estão nos JSON. Alterar `kb/` muda as respostas do sistema sem mexer no Python.

## Estrutura de pastas

```
main.py                         ponto de entrada
kb/
  fatos.json                    empresa, configuração, perguntas (entradas) e fatos derivados
  regras.json                   as 20 regras em 3 camadas
  catalogo.json                 cores, tempos de espera, textos legíveis e ordem de urgência
sistema_especialista/
  __init__.py                   descrição do pacote
  modelos.py                    estruturas de dados
  base_conhecimento.py          carga e validação da base (M1)
  incerteza.py                  fatores de certeza (M5)
  inferencia.py                 motor de inferência (M2)
  explicacao.py                 explicações "como" e "por quê" (M3)
  terminal.py                   interface de terminal (M4)
scripts/
  gerar_dicionario.py           gera docs/dicionario_regras.md a partir de kb/
tests/
  cenarios.json                 12 casos de negócio com o resultado esperado
  test_*.py                     testes de cada módulo
docs/                           esta documentação
```

---

## `kb/` — base de conhecimento (dados)

### `fatos.json`

- **`empresa`**: nome, segmento, problema e aviso legal, exibidos no cabeçalho.
- **`config`**: `limiar_cf` (0,4) e `cf_resposta_nao_sei` (0,5).
- **`entradas`**: as 9 perguntas da triagem. Cada uma tem `id` (o atributo), `pergunta` e `opcoes` (`valor` e `rotulo`). Também aceita `aplica_se` (opcional), que faz a pergunta só ser feita se uma condição valer, como `"trauma=grave"`. Nenhuma pergunta usa esse campo hoje, mas o carregador e o terminal já o suportam.
- **`derivados`**: os atributos que o motor pode concluir (`quadro`, `classificacao`, `encaminhamento`, `aviso`) e os valores possíveis de cada um.

### `regras.json`

Cada regra tem:

```json
{
  "id": "R04", "camada": 1,
  "se": ["dor_toracica=tipica", "grupo_risco=sim"],
  "entao": [{"fato": "quadro=suspeita_cardiaca", "cf": 0.6}],
  "justificativa": "Idade avançada ou doença crônica aumentam a chance..."
}
```

- `se`: lista de condições, ligadas por **E**. Dentro de uma condição, `|` significa **OU** entre valores do mesmo atributo (`febre=moderada|alta`).
- `entao`: uma ou mais conclusões, cada uma com a certeza da regra.
- `camada`: 1 (sinais → quadro), 2 (quadro → cor) ou 3 (cor → encaminhamento).
- `justificativa`: o texto usado nas explicações.

### `catalogo.json`

- `ordem_urgencia`: lista da cor mais urgente para a menos urgente, usada na resolução de conflito.
- `classificacoes`: nome e tempo máximo de espera de cada cor.
- `descricoes`: texto legível de cada fato derivado, usado pelo terminal (por exemplo, `quadro=suspeita_avc` vira "Suspeita de AVC").

---

## `sistema_especialista/modelos.py` — estruturas de dados

São todas `dataclass`es. As que descrevem a base são imutáveis (`frozen`).

| Classe | Campos | Papel |
| --- | --- | --- |
| `Condicao` | `atributo`, `valores` | Uma condição do SE. `Condicao.de_texto("febre=moderada\|alta")` cria a condição, e `fatos()` devolve `["febre=moderada", "febre=alta"]`. |
| `Conclusao` | `fato`, `cf` | Um item do ENTÃO. |
| `Regra` | `id`, `camada`, `se`, `entao`, `justificativa` | Uma regra SE/ENTÃO. |
| `Pergunta` | `atributo`, `texto`, `opcoes`, `aplica_se` | Uma pergunta da triagem. `opcoes` mapeia valor para rótulo. |
| `Disparo` | `regra_id`, `cf_condicao`, `fatos_usados`, `conclusoes` | Registro de uma regra que disparou: quais fatos satisfizeram o SE e o que ela gerou. É a matéria-prima da explicação. |
| `ResultadoInferencia` | `memoria`, `disparos`, `conclusoes` | Saída do motor: toda a memória (fato → cf), os disparos em ordem e as conclusões acima do limiar. |

## `sistema_especialista/base_conhecimento.py` — carga e validação (M1)

- **`carregar(caminho_kb=None, validar_base=True)`**: lê os três JSON (por padrão da pasta `kb/` do projeto), monta `Pergunta`s e `Regra`s e devolve uma `BaseConhecimento`. Se a validação encontra problemas, lança `BaseInvalida` com todos eles.
- **`validar(base)`**: devolve a lista de inconsistências encontradas:
  - IDs de regra repetidos;
  - `aplica_se` usando atributo desconhecido;
  - condição com atributo ou valor que não existe;
  - conclusão que não é um fato derivado declarado;
  - `cf` fora do intervalo (0, 1];
  - fato derivado sem texto em `catalogo.json → descricoes`;
  - `ordem_urgencia` que não cobre exatamente as cores;
  - **regra que usa um fato produzido na mesma camada ou numa camada posterior**, o que garante que as camadas, avaliadas em ordem, nunca dependem de algo ainda não calculado.
- **`BaseConhecimento`** oferece consultas usadas pelos outros módulos:

  | Método/propriedade | Uso |
  | --- | --- |
  | `limiar_cf`, `cf_nao_sei` | valores de `config` |
  | `eh_derivado(fato)` | separa conclusões de respostas (o motor filtra `conclusoes` com ele) |
  | `regra(id)`, `pergunta(atributo)` | busca por identificador |
  | `camadas()`, `regras_da_camada(n)` | ordem de execução do motor |
  | `regras_que_usam(atributo)` | o "por quê" de uma pergunta |
  | `regras_que_concluem(fato)` | quais regras podem produzir um fato (usado no dicionário) |

## `sistema_especialista/incerteza.py` — fatores de certeza (M5)

Três funções puras, sem dependência de outros módulos:

- `cf_condicao(cfs)`: o menor valor da lista (E lógico).
- `cf_conclusao(cf_cond, cf_regra)`: o produto dos dois.
- `combinar(a, b)`: `a + b × (1 − a)`, que é comutativa e nunca passa de 1.

Todas validam a faixa [0, 1] e lançam `ValueError` fora dela. Os exemplos numéricos estão em [motor.md](motor.md#incerteza-fatores-de-certeza).

## `sistema_especialista/inferencia.py` — motor de inferência (M2)

- **`inferir(base, respostas, cf_entradas=None)`**: faz o encadeamento para frente camada por camada e devolve um `ResultadoInferencia`.
  - `respostas` tem o formato `{"atributo": "valor"}`.
  - `cf_entradas` (opcional) traz certezas menores que 1, com chave pelo atributo (`"grupo_risco": 0.5`) ou pelo fato (`"grupo_risco=sim": 0.5`).
- **`classificacao_final(base, resultado)`**: devolve a cor mais urgente entre as conclusões, ou `None`.
- Funções internas: `_montar_memoria` transforma as respostas em fatos com certeza, e `_avaliar_se` testa se o SE de uma regra é satisfeito e calcula sua certeza.

O algoritmo passo a passo está em [motor.md](motor.md#fluxo-de-uma-consulta).

## `sistema_especialista/explicacao.py` — explicações (M3)

Trabalha só com os `Disparo`s registrados pelo motor. Nenhuma função recalcula a inferência.

| Função | O que devolve |
| --- | --- |
| `explicar_como(base, resultado, fato=None)` | Para cada regra disparada, em ordem: o ID e a camada, as **condições utilizadas** com a certeza de cada uma e as **conclusões** com o fator de certeza. Com `fato`, mostra só os disparos que produziram aquele fato. É o texto exibido no terminal quando o usuário pede o "como". |
| `explicar_por_que(base, resultado, fato)` | As regras que concluíram o `fato`, cada uma com sua **justificativa** em português e a certeza gerada. |
| `explicar_resultado(base, resultado, fato=None)` | Relatório completo que, para cada conclusão, junta a seção "1. Como o sistema chegou à conclusão" e a seção "2. Por que essa conclusão foi gerada". |

O "por quê" de uma **pergunta**, que explica por que o sistema pergunta aquilo, fica em `terminal.explicar_pergunta`, porque acontece antes da inferência.

Exemplo da saída de `explicar_como`:

```
Regra R05 (camada 1):
  Condições utilizadas: sinais_avc=sim (certeza: 100%)
  Conclusão: quadro=suspeita_avc (fator de certeza: 90%)

Regra R13 (camada 2):
  Condições utilizadas: quadro=suspeita_avc (certeza: 90%)
  Conclusão: classificacao=vermelho (fator de certeza: 86%)
```

## `sistema_especialista/terminal.py` — interface (M4)

| Função | O que faz |
| --- | --- |
| `iniciar(base=None)` | Mostra o cabeçalho e o menu em laço: **1** nova consulta, **2** ver as regras da base, **3** sair. Trata Ctrl+C e fim de entrada. |
| `exibir_cabecalho(base)` | Nome da clínica, segmento, problema e aviso legal. |
| `coletar_entradas(base)` | Percorre `base.perguntas` respeitando `aplica_se` e devolve `(respostas, cf_entradas)`. |
| `perguntar(base, pergunta)` | Mostra as opções numeradas mais "Não sei". Repete a pergunta quando a entrada é vazia, não numérica ou fora do intervalo. Com `?`, mostra o "por quê". |
| `explicar_pergunta(base, pergunta)` | Lista as regras que usam o atributo, o que cada uma ajudaria a concluir e a justificativa. |
| `exibir_resultado(base, resultado)` | Mostra a cor final com nome, certeza e tempo máximo, a observação de conflito (se houver outras cores), os quadros suspeitados, o encaminhamento e os avisos à equipe. Depois oferece o "como". Sem conclusões, informa que não foi possível concluir. |
| `exibir_regras(base)` | Lista as 20 regras por camada, no formato SE/ENTÃO, com a justificativa. |
| `limpar_tela()` | Limpa o terminal, só em sessão interativa. |

**Resposta "não sei"**, que depende do tipo de pergunta:

- **Sim/não** (`sinais_avc`, `grupo_risco`): registra `sim` com certeza 0,5. É um protocolo de segurança, porque na dúvida considera o sinal presente com certeza reduzida.
- **Outras perguntas**: pergunta qual opção parece mais provável e a registra com certeza 0,5. A opção **0** pula a pergunta, e o atributo não entra na memória.

**Cores ANSI**: são usadas só em terminal interativo e desligadas com a variável `NO_COLOR`. No Windows, usa `colorama` se estiver instalado (é opcional).

## `main.py` — ponto de entrada

Carrega a base. Se ela for inválida, mostra os erros e sai com código 1. Se não, chama `terminal.iniciar(base)`.

---

## Testes

Rode `pytest` na raiz. São 62 testes, e todos passam.

| Arquivo | O que cobre |
| --- | --- |
| `test_base_conhecimento.py` | a base sem inconsistências, 20 regras com IDs sequenciais, justificativas, 3 camadas, ordem de urgência, consultas da base |
| `test_incerteza.py` | as três fórmulas (limites 0 e 1, comutatividade, faixa inválida) e cadeias com "não sei" na base real |
| `test_inferencia.py` | os **12 cenários** de `cenarios.json` (fatos esperados, não esperados e cor final), memória, limiar, combinação, ordem dos disparos e caso sem alerta |
| `test_explicacao.py` | conteúdo do "como", do "por quê" e do relatório completo, filtro por fato e caso sem conclusões |
| `test_terminal.py` | cabeçalho, validação de entradas, `?`, "não sei" nos dois tipos de pergunta, `aplica_se`, exibição de resultado (com conflito, avisos e sem conclusão), menu, `main` com base inválida e limpeza de tela |

### `tests/cenarios.json`

São os casos de negócio que o sistema precisa acertar. Cada um tem `entradas`, `cf_entradas` (opcional), `esperado` (fatos que precisam estar nas conclusões), `nao_esperado` (opcional) e `classificacao_final`. Para incluir um caso novo, basta acrescentá-lo ao arquivo: o teste é parametrizado.

## Como estender

| Quero… | Faça |
| --- | --- |
| Nova pergunta | Acrescente em `fatos.json → entradas` e use o atributo nas regras. |
| Nova regra | Acrescente em `regras.json` respeitando as camadas. O carregador recusa a regra se ela usar um fato da mesma camada ou de uma camada posterior. Depois, ajuste `test_tem_exatamente_20_regras`. |
| Novo quadro, cor ou aviso | Inclua o valor em `fatos.json → derivados` **e** o texto em `catalogo.json → descricoes`. Para uma cor, inclua também `classificacoes` e `ordem_urgencia`. |
| Mudar limiar ou "não sei" | `fatos.json → config` |
| Atualizar o dicionário | `python scripts/gerar_dicionario.py` |
