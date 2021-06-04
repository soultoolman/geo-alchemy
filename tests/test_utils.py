# -*- coding: utf-8 -*-
from datetime import date

from lxml import etree

from geo_alchemy.utils import remove_namespace, date_from_geo_string


def test_remove_namespace(sample_miniml):
    element = etree.fromstring(sample_miniml)
    assert element.tag == '{http://www.ncbi.nlm.nih.gov/geo/info/MINiML}MINiML'
    remove_namespace(element)
    assert element.tag == 'MINiML'


def test_date_from_geo_string():
    assert date_from_geo_string(
        '2021-05-21'
    ) == date(2021, 5, 21)
