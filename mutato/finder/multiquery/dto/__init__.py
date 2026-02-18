# !/usr/bin/env python
# -*- coding: UTF-8 -*-


def cleanse_canon(input_text: str) -> str:
    if ' ' in input_text:
        input_text = input_text.replace(' ', '_')
    if "'" in input_text:
        input_text = input_text.replace("'", '')
    return input_text.lower().strip()
