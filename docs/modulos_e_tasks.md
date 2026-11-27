# Módulos e tasks

Parte técnica do projeto, em sete módulos (M0 a M6). Vídeo, PDF e entrega ficam fora deste documento.

**Ordem recomendada:** M0, M1, M5, M2, M3, M4, M6. A incerteza (M5) vem antes do motor (M2) porque o motor usa as três fórmulas dela.

| Módulo | O que é | Responsável | Status |
| --- | --- | --- | --- |
| M0 | Repositório e fluxo de trabalho | ______ | concluído |
| M1 | Base de conhecimento (fatos e regras) | ______ | concluído |
| M5 | Incerteza (fator de certeza) | ______ | concluído |
| M2 | Motor de inferência | ______ | concluído |
| M3 | Explicação ("como" e "por quê") | ______ | concluído |
| M4 | Interface de terminal | ______ | concluído |
| M6 | Documentação técnica | ______ | concluído |

## M0 — Repositório e fluxo de trabalho (concluído)

**Pronto quando:** todos clonam, criam o ambiente e conseguem dar push numa branch própria.

**Por quê:** o professor exige repositório no GitHub e confere o histórico de commits; quem quase não aparece pode ter a nota individual reduzida.

- [x] Estrutura inicial commitada (`README.md`, `requirements.txt`, `pytest.ini`, `.gitignore`, pacote e pastas)
- [x] Criar o repositório no GitHub, adicionar o remote e fazer o push do commit inicial
- [x] Deixar o repositório público (ou liberar o professor) e adicionar os integrantes como colaboradores
- [x] Cada integrante: clonar, configurar `git config user.name` e `user.email` reais, criar o ambiente (`python -m venv .venv` e `pip install -r requirements.txt`)
- [x] Combinar o fluxo: uma branch por módulo, commits pequenos no padrão Conventional Commits (`feat`, `fix`, `test`, `docs`, `chore`), sem Co-Authored-By, merge só com `pytest` passando
- [x] Preencher os responsáveis na tabela do `README.md`

## M1 — Base de conhecimento (concluído)

**Pronto quando:** o grupo revisou as 20 regras e cada integrante explica as três camadas.

**Como foi feito:** um fato é um texto `atributo=valor`; uma regra é SE (condições) ENTÃO (conclusões com certeza). As 20 regras formam três camadas: R01–R12 levam os sinais a um quadro, R13–R17 levam o quadro a uma cor de risco, R18–R20 levam a cor ao encaminhamento. A base fica em arquivos JSON e é validada ao carregar.

- [x] `modelos.py`: estruturas de dados (`Condicao`, `Conclusao`, `Regra`, `Pergunta`, `Disparo`, `ResultadoInferencia`)
- [x] `base_conhecimento.py`: carga e validação da base
- [x] `kb/fatos.json`, `kb/regras.json` e `kb/catalogo.json` (20 regras)
- [x] Revisar o conteúdo clínico (sinais, cores, tempos), mantendo 20 regras
- [x] `tests/test_base_conhecimento.py` e `tests/cenarios.json` (12 cenários)
- [x] Base congelada antes de implementar o motor

## M5 — Incerteza (fator de certeza) (concluído)

**Arquivo:** `sistema_especialista/incerteza.py` · **Pronto quando:** as fórmulas passam em `tests/test_incerteza.py`.

**Como fazer:** são três funções curtas. A certeza da condição é o menor valor entre as condições; a da conclusão é essa certeza vezes a da regra; quando duas regras concluem o mesmo fato, combina-se `a + b × (1 − a)` (0,6 e 0,8 dão 0,92). Resposta "não sei" entra com certeza 0,5.

- [x] Implementar `cf_condicao`, `cf_conclusao` e `combinar`
- [x] Criar `tests/test_incerteza.py` e fazer passar
- [x] Escrever pelo menos 3 testes novos (ex.: "não sei" em tudo, valores nos limites 0 e 1)
- [x] (Opcional) Dados: `kb/historico_atendimentos.csv` fictício e tempo médio de espera por cor

## M2 — Motor de inferência (concluído)

**Arquivo:** `sistema_especialista/inferencia.py` · **Pronto quando:** os 12 cenários de `tests/test_inferencia.py` passam.

**Como fazer:** encadeamento **para frente**: parte dos fatos informados e dispara regras camada por camada (1, 2, 3), guardando na memória cada conclusão com sua certeza. Quando mais de uma cor passa do limiar (0,4), vale a mais **urgente**, não a de maior certeza (`classificacao_final`).

- [x] Implementar `inferir`: memória `atributo=valor` com certeza, entradas com 1,0 (ou o valor de `cf_entradas`), camadas em ordem, combinação quando duas regras concluem o mesmo fato
- [x] Registrar um `Disparo` por regra disparada (a explicação depende disso)
- [x] Preencher `conclusoes` só com fatos derivados acima do `limiar_cf`
- [x] Implementar `classificacao_final` pela ordem de urgência do catálogo (`None` se não houver cor)
- [x] Criar `tests/test_inferencia.py` e rodar `pytest`
- [x] Registrar em `docs/motor.md` o tipo de encadeamento, o fluxo de uma consulta e a resolução de conflito

## M3 — Explicação ("como" e "por quê") (concluído)

**Arquivo:** `sistema_especialista/explicacao.py` · **Pronto quando:** toda conclusão vem com a justificativa em português legível.

**Como fazer:** o professor dá peso relevante a este módulo. **"Como?"** mostra a cadeia de regras e fatos que levou à conclusão; **"Por quê?"** mostra por que o sistema está fazendo aquela pergunta agora.

- [x] `explicar_como(base, resultado, fato)`: montar a cadeia a partir dos `disparos`, usando a `justificativa` de cada regra e separando o que foi informado do que foi deduzido
- [x] `terminal.explicar_pergunta(base, pergunta)` ("por quê" da pergunta): listar as regras que usam a pergunta (`base.regras_que_usam`) e o que cada uma ajudaria a concluir
- [x] `explicar_resultado` e `explicar_por_que`: o "como" e a justificativa de cada conclusão
- [x] Mostrar a certeza em % ao lado de cada conclusão
- [x] Testar com 3 cenários (idoso com dor no peito, acidente de moto, febre alta com confusão) e conferir o texto contra o JSON

## M4 — Interface de terminal (concluído)

**Arquivos:** `sistema_especialista/terminal.py` e `main.py` · **Pronto quando:** uma pessoa leiga faz uma consulta completa sem ajuda.

**Como fazer:** sem interface gráfica; o enunciado aceita terminal desde que o fluxo de perguntas e respostas seja claro. O cabeçalho com empresa, problema e aviso legal cumpre a contextualização de negócio.

- [x] `iniciar`: menu em laço (nova consulta, ver as regras da base, sair)
- [x] `perguntar`: opções numeradas e validação (vazio, fora das opções, texto), repetindo a pergunta com mensagem clara; opção "não sei"
- [x] `coletar_entradas`: percorrer `base.perguntas` respeitando `aplica_se`; "não sei" vira `base.cf_nao_sei`; `?` mostra o "por quê" (M3)
- [x] `exibir_resultado`: cor, tempo máximo de espera, quadros suspeitados, encaminhamento e avisos, com a certeza em %; opção de ver o "como"
- [x] Mensagem "Não foi possível concluir com as informações fornecidas" quando não há conclusão
- [x] Rodar à mão os cenários de `cenarios.json`

## M6 — Documentação técnica (concluído)

**Arquivos:** `README.md` e `docs/` · **Pronto quando:** alguém de fora entende o projeto lendo o README e a pasta `docs/`.

- [x] `docs/contexto_negocio.md`: empresa, problema e aviso legal
- [x] Dicionário de fatos e regras gerado dos JSON (`scripts/gerar_dicionario.py`)
- [x] `docs/motor.md`: tipo de encadeamento, memória de trabalho, fluxo de uma consulta, resolução de conflito, incerteza e casos de exceção
- [x] Manter a tabela de módulos e o "como rodar" do README atualizados
- [x] Revisão: um integrante que não escreveu cada documento lê e aponta o que não entendeu
