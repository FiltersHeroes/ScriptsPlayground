#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=C0103
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring

import os

KAD_matrix_strategy = []
for i in range(1, int(os.getenv("NUMBER_OF_KAD_JOBS")) + 1):
    KAD_matrix_strategy.append(i)

KADhosts_matrix_strategy = []
for i in range(1, int(os.getenv("NUMBER_OF_KADHOSTSWWW_JOBS")) + 1):
    KADhosts_matrix_strategy.append(i)

with open(os.getenv("GITHUB_OUTPUT"), "a") as gho:
    print(f"KAD-strategy-matrix={KAD_matrix_strategy}", file=gho)
    print(f"KADh-strategy-matrix={KADhosts_matrix_strategy}", file=gho)
