import logging

from odoo import models

_logger = logging.getLogger(__name__)

ALPHABETS = {
    'ru': 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя',
    'ua': 'абвгґдеєжзиіїйклмнопрстуфхцчшщьюя',
    'uk': 'абвгґдеєжзиіїйклмнопрстуфхцчшщьюя',
}


def alphabet_sorted(vals, index, alphabet='', symbols=''):
    if not symbols:
        if alphabet not in ALPHABETS.keys():
            return sorted(vals, key=lambda k: k[index])
        symbols = ALPHABETS[alphabet].lower()
    symbols = symbols.upper() + symbols
    tr = {}
    for i in symbols:
        if symbols.index(i):
            tr[ord(i)] = ord('А') + symbols.index(i)
        else:
            tr[ord(i)] = ord(i)

    def translate(name):
        return name.translate(tr)

    return sorted(vals, key=lambda k: translate(k[index]))


class AlphabetSortedMixin(models.AbstractModel):
    _name = 'kw.alphabet.sorted.mixin'
    _description = 'Sort by alphabet'

    @staticmethod
    def alphabet_sorted(vals, index, alphabet='', symbols=''):
        return alphabet_sorted(vals, index, alphabet, symbols)
