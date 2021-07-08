# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import math
from collections import Counter


def set_entropy(string_meta_analysis, string_value):
    """
    Sets the entropy of a string.
    :param string_meta_analysis: class:'StringMetaAnalysis'
    :param string_value: str - string value to test.
    """
    string_meta_analysis.natural_entropy = calculate_entropy(string_value, 'natural')
    string_meta_analysis.shannon_entropy = calculate_entropy(string_value, 'shannon')
    string_meta_analysis.hartley_entropy = calculate_entropy(string_value, 'hartley')
    logging.info(f"natural_entropy {string_meta_analysis.natural_entropy} "
                 f"shannon_entropy {string_meta_analysis.shannon_entropy} "
                 f"hartley_entropy {string_meta_analysis.hartley_entropy} ")


def calculate_entropy(data, unit):
    """
    Calculates the entropy of a given string.
    :param data: str - the string to calculate the entropy from.
    :param unit: str - the entropy type to calculate (shannon, natural or hartley)
    :return: float - entropy
    """
    if len(data) <= 1:
        return 0
    if not unit:
        unit = 'natural'
    base = {
        'shannon': 2.,
        'natural': math.exp(1),
        'hartley': 10.
    }
    counts = Counter()
    for d in data:
        counts[d] += 1
    ent = 0
    probs = [float(c) / len(data) for c in counts.values()]
    for p in probs:
        if p > 0.:
            ent -= p * math.log(p, base[unit])
    return ent
