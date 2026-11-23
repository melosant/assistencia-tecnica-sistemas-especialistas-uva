"""Ponto de entrada do Sistema Especialista de triagem de risco (Clínica Vida Plena)."""
from __future__ import annotations

import sys

from sistema_especialista.base_conhecimento import BaseInvalida, carregar
from sistema_especialista.terminal import iniciar


def main() -> int:
    try:
        base = carregar()
    except BaseInvalida as erro:
        print(f"Erro ao carregar a base de conhecimento:\n{erro}", file=sys.stderr)
        return 1
    iniciar(base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
