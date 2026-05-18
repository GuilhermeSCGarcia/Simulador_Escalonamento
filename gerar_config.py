#!/usr/bin/env python3
"""Gera um arquivo de configuração (.txt) com muitas tarefas.

Formato gerado (compatível com `CarregarConfig.py`):
- Linha 0: algoritmo;quantum;qtde_cpus
- Demais: id;cor;ingresso;tempoTotal;prioridade;[]

Exemplos:
  python gerar_config.py --out config_massivo.txt --n 200 --cpus 4 --alg SRTF --quantum 2
  python gerar_config.py --out config_burst.txt --n 500 --ingresso-max 50 --dur-min 1 --dur-max 40 --seed 123
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass


CORES_SUGESTAO = [
    "FF6B6B",  # vermelho suave
    "4ECDC4",  # verde-água
    "45B7D1",  # azul
    "F7B801",  # amarelo
    "A29BFE",  # roxo
    "FF8C42",  # laranja
    "2ECC71",  # verde
    "E84393",  # rosa
]


@dataclass(frozen=True)
class Args:
    out: str
    n: int
    alg: str
    quantum: int
    cpus: int
    id_start: int
    ingresso_min: int
    ingresso_max: int
    dur_min: int
    dur_max: int
    prio_min: int
    prio_max: int
    seed: int | None


def _parse_args() -> Args:
    p = argparse.ArgumentParser(description="Gerador de config massiva para o simulador")
    p.add_argument("--out", required=True, help="Caminho do arquivo .txt de saída")
    p.add_argument("--n", type=int, required=True, help="Quantidade de tarefas")

    p.add_argument("--alg", default="SRTF", help="Algoritmo (ex: SRTF, RR, etc.)")
    p.add_argument("--quantum", type=int, default=2, help="Quantum do sistema")
    p.add_argument("--cpus", type=int, default=2, help="Quantidade de CPUs")

    p.add_argument("--id-start", type=int, default=1, help="ID inicial (default: 1)")

    p.add_argument("--ingresso-min", type=int, default=0, help="Tick mínimo de ingresso")
    p.add_argument("--ingresso-max", type=int, default=0, help="Tick máximo de ingresso (default: 0 = tudo no t=0)")

    p.add_argument("--dur-min", type=int, default=1, help="Duração mínima (tempoTotal)")
    p.add_argument("--dur-max", type=int, default=20, help="Duração máxima (tempoTotal)")

    p.add_argument("--prio-min", type=int, default=1, help="Prioridade mínima")
    p.add_argument("--prio-max", type=int, default=5, help="Prioridade máxima")

    p.add_argument("--seed", type=int, default=None, help="Seed do RNG para reprodutibilidade")

    ns = p.parse_args()

    if ns.n <= 0:
        raise SystemExit("--n precisa ser > 0")
    if ns.cpus <= 0:
        raise SystemExit("--cpus precisa ser > 0")
    if ns.quantum <= 0:
        raise SystemExit("--quantum precisa ser > 0")
    if ns.dur_min <= 0 or ns.dur_max <= 0 or ns.dur_min > ns.dur_max:
        raise SystemExit("Faixa inválida: --dur-min/--dur-max")
    if ns.ingresso_min < 0 or ns.ingresso_max < 0 or ns.ingresso_min > ns.ingresso_max:
        raise SystemExit("Faixa inválida: --ingresso-min/--ingresso-max")
    if ns.prio_min <= 0 or ns.prio_max <= 0 or ns.prio_min > ns.prio_max:
        raise SystemExit("Faixa inválida: --prio-min/--prio-max")

    return Args(
        out=ns.out,
        n=ns.n,
        alg=str(ns.alg).upper(),
        quantum=ns.quantum,
        cpus=ns.cpus,
        id_start=ns.id_start,
        ingresso_min=ns.ingresso_min,
        ingresso_max=ns.ingresso_max,
        dur_min=ns.dur_min,
        dur_max=ns.dur_max,
        prio_min=ns.prio_min,
        prio_max=ns.prio_max,
        seed=ns.seed,
    )


def _cor_por_indice(i: int) -> str:
    # Cicla pelas cores sugeridas.
    return CORES_SUGESTAO[i % len(CORES_SUGESTAO)]


def main() -> int:
    args = _parse_args()

    rng = random.Random(args.seed)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(f"{args.alg};{args.quantum};{args.cpus}\n")

        for idx in range(args.n):
            task_id = args.id_start + idx
            cor = _cor_por_indice(idx)
            ingresso = rng.randint(args.ingresso_min, args.ingresso_max)
            tempo_total = rng.randint(args.dur_min, args.dur_max)
            prioridade = rng.randint(args.prio_min, args.prio_max)

            # Campo listaEvento: mantenho como '[]' (string) para compatibilidade com o parser atual.
            f.write(f"{task_id};{cor};{ingresso};{tempo_total};{prioridade};[]\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
