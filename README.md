# Clínica Vida Plena — Sistema Especialista de Triagem de Risco

Trabalho avaliativo de **Programação de Sistemas Especialistas** (UVA, Ciência da Computação). Prazo: **28/11/2026, 23:59**.

Protótipo de sistema especialista para o pronto atendimento de uma clínica fictícia. O profissional de triagem responde perguntas no terminal e o sistema classifica o risco por cores (vermelho, laranja, amarelo, verde), indica o encaminhamento e os avisos à equipe, explicando o raciocínio e a certeza de cada conclusão.

> **Aviso:** protocolo simplificado e fictício, criado para fins acadêmicos. É uma ferramenta de apoio e não substitui a avaliação de um profissional de saúde.

Contexto de negócio completo: [docs/contexto_negocio.md](docs/contexto_negocio.md).

Módulos e tasks: [docs/modulos_e_tasks.md](docs/modulos_e_tasks.md).

## Como rodar

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (no Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt

python main.py                # executa o sistema
pytest                        # roda os testes
python scripts/gerar_dicionario.py   # atualiza docs/dicionario_regras.md
```

## Estrutura

```
main.py                        ponto de entrada (terminal)
kb/                            base de conhecimento, lida de arquivos (sem mexer no código)
  fatos.json                   empresa, perguntas, fatos derivados, limiar de certeza
  regras.json                  20 regras em 3 camadas
  catalogo.json                cores, tempos de espera, textos e ordem de urgência (fictícios)
sistema_especialista/
  modelos.py                   estruturas de dados
  base_conhecimento.py         leitura e validação da base            (pronto)
  incerteza.py                 fatores de certeza                      (M5)
  motor.py                     encadeamento para frente                (M2)
  explicacao.py                "como" e "por quê"                      (M3)
  terminal.py                  perguntas e respostas no terminal       (M4)
tests/
  cenarios.json                12 casos de negócio com a conclusão esperada
  test_base_conhecimento.py    valida a base (já passa)
  test_incerteza.py            fórmulas de certeza (M5)
  test_cenarios.py             cenários contra o motor (M2)
docs/                          contexto de negócio, dicionário de regras, descrição do motor
scripts/gerar_dicionario.py    gera docs/dicionario_regras.md a partir de kb/
```

## Como o sistema raciocina (resumo)

- Um **fato** é um texto `atributo=valor` (ex.: `sinais_avc=sim`, `quadro=suspeita_avc`).
- Uma **regra** diz: SE todas as condições valem, ENTÃO conclui fatos novos, cada um com uma certeza (`cf`).
- As regras ficam em **3 camadas**: sinais levam a um quadro de triagem (R01–R12), o quadro leva à classificação por cor (R13–R17) e a cor leva ao encaminhamento (R18–R20). Isso cria cadeias de 3 passos.
- O motor percorre as camadas em ordem (**encadeamento para frente**) e acumula as conclusões na memória de trabalho.
- A certeza de uma conclusão = menor certeza das condições × certeza da regra. Quando duas regras concluem o mesmo fato, as certezas se combinam por `a + b × (1 − a)`.
- Conclusões com certeza abaixo de 0,4 não são apresentadas. Se nada passa do limiar, o sistema informa que não foi possível concluir.
- **Conflito:** várias cores podem passar do limiar ao mesmo tempo. Vale a **mais urgente**, não a de maior certeza: na dúvida, o paciente sobe de nível.

## Divisão de módulos

Todo integrante precisa entender **todos** os módulos: no vídeo, o professor pode cobrar qualquer trecho de qualquer pessoa.

| Módulo | O que é | Responsável | Status |
| --- | --- | --- | --- |
| M0 | Repositório, estrutura, README | ______ | concluído |
| M1 | Base de conhecimento (20 regras, fatos, catálogo) | ______ | concluído |
| M2 | Motor de inferência (`motor.py`) | ______ | a fazer |
| M3 | Explicação "como" e "por quê" (`explicacao.py`) | ______ | a fazer |
| M4 | Interface de terminal (`terminal.py`) | ______ | a fazer |
| M5 | Diferenciais: incerteza, testes, dados (`incerteza.py`, `tests/`) | ______ | a fazer |
| M6 | Documentação (`docs/`) | ______ | a fazer |
| M7 | Vídeo de 9 a 11 min, PDF e envio no Teams | ______ | a fazer |

## Regras de trabalho do grupo

- Cada pessoa trabalha em uma **branch própria** (`m2-motor`, `m3-explicacao`...) e abre merge para `main` quando o módulo estiver funcionando.
- **Commits pequenos e frequentes**, com mensagem clara. O professor avalia o histórico para ver a contribuição de cada integrante.
- Todos usam o nome e o e-mail reais no Git (`git config user.name` e `user.email`).
- Antes de fazer merge, rode `pytest` e `python main.py`. Aplicação que não roda recebe nota zero.
- Os testes de `test_incerteza.py` e `test_cenarios.py` estão marcados como `xfail` até os módulos serem implementados. **Remova a linha `pytestmark`** de cada arquivo quando os testes passarem.

## Entrega

PDF com nomes completos dos participantes, link do repositório e link do vídeo, enviado por um único integrante ao Teams (local **Trabalhos**).
