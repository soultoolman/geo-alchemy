# -*- coding: utf-8 -*-
import re
import logging
from os.path import basename, join

import click
import pandas as pd

from .geo import geo_router
from .exceptions import GeoAlchemyError
from .parsers import (
    PlatformParser,
    SeriesParser,
)
from .utils import (
    SOFT_COMMIT_CHAR,
    AGG_FUNCS,
    DEFAULT_RETRIES,
    NcbiFtp,
    HttpDownloader,
    AsperaDownloader,
    can_be_used,
    DEFAULT_REMAIN_SECONDS,
    print_ocmir,
)


logger = logging.getLogger('geo-alchemy')


def series_accession_checker(ctx, param, value):
    if not re.search(r'^GSE\d+$', value):
        raise click.UsageError(f'Invalid Series accession {value}')
    return value


def platform_accession_checker(ctx, param, value):
    if not re.search(r'^GPL\d+$', value):
        raise click.UsageError(f'Invalid Series accession {value}')
    return value


@click.group()
@click.option(
    '-d', '--debug-mode', is_flag=True,
    help='enable debug mode'
)
@click.option(
    '-l', '--log-file', type=click.Path(exists=False),
    default='geo-alchemy.log', show_default=True, help='log file'
)
def geo_alchemy(debug_mode, log_file):
    """
    geo-alchemy command line suite
    """
    level = logging.DEBUG if debug_mode else logging.WARNING
    logging.basicConfig(level=level, filename=log_file)


@geo_alchemy.command(name='pp')
@click.option(
    '-s', '--series', 'series_accession', required=True,
    callback=series_accession_checker, help='series accession'
)
@click.option(
    '-p', '--platform', 'platform_accession', required=True,
    callback=platform_accession_checker, help='platform accession'
)
@click.option(
    '--cache-dir', default='.', type=click.Path(exists=True),
    help='cache directory, when file existed in cache directory, network downloading will be omitted.'
)
@click.option(
    '-g', '--gene', 'gene_col', required=True, type=click.IntRange(min=2),
    help='in platform annotation file, which column is gene.'
)
@click.option(
    '-a', '--aggregate-function', default='median',
    show_default=True, type=click.Choice(AGG_FUNCS),
    help='when multiple probes map to same gene, which aggregate method will be used for merging.'
)
@click.option(
    '-c', '--clinical', 'clinical_file',
    default='{accession}_clinical.txt', show_default=True, help='output clinical file'
)
@click.option(
    '-e', '--expression', 'expression_file',
    default='{accession}_expression.txt', show_default=True, help='output gene expression file.'
)
@click.option(
    '--ocmir', is_flag=True,
    help="if you're using OCM, enable this option makes geo-alchemy print intermediate results."
)
def geo_alchemy_pp(
    series_accession,
    platform_accession,
    cache_dir,
    gene_col,
    aggregate_function,
    clinical_file,
    expression_file,
    ocmir
):
    """
    series preprocessing:
    generate phenotype file and gene expression file
    """
    try:
        print_ocmir('accession', series_accession, ocmir)
        print_ocmir('platform_accession', platform_accession, ocmir)
        # 1. initialize downloader
        aspera_downloader = AsperaDownloader(DEFAULT_RETRIES)
        http_downloader = HttpDownloader(DEFAULT_RETRIES)

        # 1. obtain platform metadata
        print('Obtaining platform metadata...')
        platform_file = join(cache_dir, f'{platform_accession}.xml')
        if not can_be_used(platform_file, DEFAULT_REMAIN_SECONDS):
            http_downloader.dl(
                geo_router.platform_detail(platform_accession, view='full'),
                outfile=platform_file
            )
        platform = PlatformParser.from_miniml_file(platform_file).parse()
        mapping = pd.Series(platform.get_probe_gene_mapping(gene_col-1))

        # 2. obtain series metadata
        print('Obtaining series metadata...')
        series_file = join(cache_dir, f'{series_accession}.xml')
        if not can_be_used(series_file, DEFAULT_REMAIN_SECONDS):
            http_downloader.dl(
                geo_router.series_detail(series_accession),
                outfile=series_file
            )
        series = SeriesParser.from_miniml_file(series_file).parse()
        is_array = False
        for experiment_type in series.experiment_types:
            if experiment_type.title == 'Expression profiling by array':
                is_array = True
                break
        if not is_array:
            raise GeoAlchemyError('Expression profiling by array series only.')
        clinical = pd.DataFrame(series.clinical)

        # 3. download series matrix file
        print('Obtaining series matrix...')
        with NcbiFtp() as ftp:
            if aspera_downloader.check():
                downloader = aspera_downloader
                url = ftp.series_matrix_file_aspera_url(series_accession, platform_accession)
            else:
                downloader = http_downloader
                url = ftp.series_matrix_file_url(series_accession, platform_accession)
        probe_file = join(cache_dir, basename(url))
        if not can_be_used(probe_file):
            downloader.dl(url, probe_file)
        probe = pd.read_table(probe_file, comment=SOFT_COMMIT_CHAR, index_col=0)
        print_ocmir('probe_count', probe.shape[0], ocmir)
        print_ocmir('sample_count', probe.shape[1], ocmir)

        # 3. probe to gene
        print('Converting probe to gene...')
        gene = getattr(probe.groupby(mapping), aggregate_function)()
        print_ocmir('gene_count', gene.shape[0], ocmir)

        # 4. save to file
        print('Saving to file...')
        clinical_file = clinical_file.format(accession=series_accession)
        expression_file = expression_file.format(accession=series_accession)
        clinical.to_csv(clinical_file, sep='\t', index=False)
        gene.to_csv(
            expression_file,
            sep='\t',
            index_label=platform.columns[gene_col-1].name
        )
    except GeoAlchemyError as exc:
        logger.exception(exc)
        raise click.UsageError(str(exc))
    except Exception as exc:
        logger.exception(exc)
        raise click.UsageError('Unknown error occurred, refer to log file for details.')


if __name__ == '__main__':
    geo_alchemy()
