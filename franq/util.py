# -*- coding: utf-8 -*-


def counter(start=1, step=1):
    page = start
    while True:
        yield page
        page += 1
