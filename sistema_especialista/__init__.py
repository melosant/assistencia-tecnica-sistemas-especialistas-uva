"""Sistema Especialista de triagem de risco da Clínica Vida Plena (pronto atendimento).

Módulos:
    modelos             estruturas de dados (Condicao, Regra, Disparo, ...)
    base_conhecimento   leitura e validação dos JSON da pasta kb/          (M1)
    incerteza           fórmulas de fator de certeza                        (M5)
    motor               motor de inferência (encadeamento para frente)      (M2)
    explicacao          explicações "como" e "por quê"                      (M3)
    terminal            interface de perguntas e respostas no terminal      (M4)
"""
