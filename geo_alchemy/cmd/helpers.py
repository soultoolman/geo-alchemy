# -*- coding: utf-8 -*-
import re
import json
import codecs
import logging
import subprocess as sp

import click
import pandas as pd

from ..parsers import SeriesParser


logger = logging.getLogger('geo-alchemy')


def series_accession_checker(ctx, param, value):
    if value is None:
        return None
    if not re.search(r'^GSE\d+$', value):
        raise click.UsageError(f'Invalid Series accession {value}')
    return value


def platform_accession_checker(ctx, param, value):
    if value is None:
        return None
    if not re.search(r'^GPL\d+$', value):
        raise click.UsageError(f'Invalid platform accession {value}')
    return value


def check_blast_installation():
    try:
        sp.run(['blastn', '-help'], stderr=sp.PIPE, stdout=sp.PIPE)
    except Exception:
        raise click.UsageError('BLAST not installed.')


class Align(object):
    def __init__(self, qseqid, sseqid, evalue, pident, qcovhsp):
        self.qseqid = qseqid
        self.sseqid = sseqid
        self.evalue = float(evalue)
        self.pident = float(pident)
        self.qcovhsp = float(qcovhsp)

    def check_evalue(self, evalue=1e-5):
        return self.evalue <= evalue

    def check_pident(self, pident=100.0):
        return self.pident >= pident

    def check_qcovhsp(self, qcovhsp=100.0):
        return self.qcovhsp >= qcovhsp

    def check(self, evalue=1e-5, pident=100.0, qcovhsp=100.0):
        return self.check_evalue(
            evalue
        ) and self.check_pident(
            pident
        ) and self.check_qcovhsp(
            qcovhsp
        )

    @classmethod
    def parse_line(cls, line):
        qseqid, sseqid, evalue, pident, qcovhsp = line.rstrip().split('\t')
        return cls(qseqid, sseqid, evalue, pident, qcovhsp)

    @classmethod
    def parse_file(cls, file):
        with codecs.open(file) as fp:
            return [cls.parse_line(line) for line in fp]


def get_mapping(ctx, param, value):
    if value is None:
        return None
    try:
        mapping = {}
        with codecs.open(value, encoding='utf-8') as fp:
            fp.readline()
            for line in fp:
                probe_id, gene_symbol = line.rstrip().split('\t')
            mapping[probe_id] = gene_symbol
        return pd.Series(mapping)
    except Exception:
        raise click.UsageError(f'Invalid mapping file {value}')


def get_series_from_accession(ctx, param, value):
    if value is None:
        return None
    try:
        return SeriesParser.from_accession(value).parse()
    except Exception:
        raise click.UsageError(f"Can't parse {value}")


def get_series_from_file(ctx, param, value):
    if value is None:
        return None
    try:
        with codecs.open(value, encoding='utf-8') as fp:
            data = json.load(fp)
        return SeriesParser.parse_dict(data)
    except Exception:
        raise click.UsageError(f"Can't parse series file {value}")
