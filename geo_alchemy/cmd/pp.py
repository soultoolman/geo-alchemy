# -*- coding: utf-8 -*-
import logging
from os.path import basename, join

import click
import pandas as pd

from ..geo import geo_router
from ..parsers import PlatformParser
from ..exceptions import GeoAlchemyError
from .helpers import (
    get_series_from_accession,
    get_series_from_file,
    platform_accession_checker,
    get_mapping,
)
from ..utils import (
    SOFT_COMMIT_CHAR,
    AGG_FUNCS,
    NcbiFtp,
    can_be_used,
    DEFAULT_REMAIN_SECONDS,
    print_ocmir,
    http_downloader,
    aspera_downloader
)


logger = logging.getLogger('geo-alchemy')


@click.option(
    '-s', '--series', 'series_from_accession',
    required=False,
    callback=get_series_from_accession,
    help='series accession, if not provided, -sf should be provided.'
)
@click.option(
    '-sf', '--series-file', 'series_from_file',
    required=False,
    callback=get_series_from_file,
    help='series serialized file, if not provided, -s should be provided.'
)
@click.option(
    '-p', '--platform', 'platform_accession',
    required=False,
    callback=platform_accession_checker,
    help='platform accession, must be provided when series has multiple platforms.'
)
@click.option(
    '-m', '--mapping-file', 'mapping',
    required=False,
    callback=get_mapping,
    help=(
        "probe ID gene symbol mapping file, "
        "first row is headers, "
        "first column is probe ID, "
        "second column is gene symbol. "
        "If you don't want download platform annotation data "
        "using network, this file can be provided."
    )
)
@click.option(
    '-g', '--gene', 'gene_col',
    required=False, type=click.IntRange(min=2),
    help='in platform annotation file, which column is gene, need when -m not provided.'
)
@click.option(
    '-a', '--aggregate-function',
    default='median',
    show_default=True,
    type=click.Choice(AGG_FUNCS),
    help='when multiple probes map to same gene, which aggregate method will be used for merging.'
)
@click.option(
    '-c', '--clinical', 'clinical_file',
    default='{accession}_clinical.txt',
    show_default=True,
    help='output clinical file'
)
@click.option(
    '-e', '--expression', 'expression_file',
    default='{accession}_expression.txt', show_default=True, help='output gene expression file.'
)
@click.option(
    '--cache-dir',
    default='.',
    show_default=True,
    type=click.Path(exists=True),
    help='cache directory, when file existed in cache directory, network downloading will be omitted.'
)
@click.option(
    '--ocmir',
    is_flag=True,
    help="if you're using OCM, enable this option makes geo-alchemy print intermediate results."
)
def pp(
    series_from_accession,
    series_from_file,
    platform_accession,
    mapping,
    gene_col,
    aggregate_function,
    clinical_file,
    expression_file,
    cache_dir,
    ocmir
):
    """
    series preprocessing:
    generate phenotype file and gene expression file
    """
    try:
        series = None
        if series_from_accession:
            series = series_from_accession
        if series_from_file:
            series = series_from_file
        if not series:
            raise click.UsageError('Either -s or -sf should be provided.')
        if series.is_malformed:
            raise click.UsageError(f'Malformed series {series.accession}')
        is_array = False
        for experiment_type in series.experiment_types:
            if experiment_type.title == 'Expression profiling by array':
                is_array = True
                break
        if not is_array:
            raise click.UsageError('Expression profiling by array series only.')
        platforms = series.platforms
        if not platforms:
            raise click.UsageError(f'Malformed series {series.accession}')
        if len(platforms) == 1:
            platform = platforms[0]
        else:
            if not platform_accession:
                raise click.UsageError(
                    f'Multiple platforms found in {series.accession}, '
                    f'-p must be provided.'
                )
            platform = None
            for temp in platforms:
                if temp.accession == platform_accession:
                    platform = temp
                    break
            if not platform:
                raise click.UsageError(f'Platform {platform_accession} not found in series {series.accession}.')
        clinical = pd.DataFrame(series.get_platform_clinical(platform))
        print_ocmir('accession', series.accession, ocmir)
        print_ocmir('platform_accession', platform.accession, ocmir)

        if mapping is None:
            if not gene_col:
                raise click.UsageError('-g must be provided.')
            platform_file = join(cache_dir, f'{platform.accession}.xml')
            if not can_be_used(platform_file, DEFAULT_REMAIN_SECONDS):
                http_downloader.dl(
                    geo_router.platform_detail(platform.accession, view='full'),
                    outfile=platform_file
                )
            platform = PlatformParser.from_miniml_file(platform_file).parse(lazy=False)
            mapping = pd.Series(platform.get_probe_gene_mapping(gene_col-1))

        with NcbiFtp() as ftp:
            if aspera_downloader.check():
                downloader = aspera_downloader
                url = ftp.series_matrix_file_aspera_url(series.accession, platform.accession)
            else:
                downloader = http_downloader
                url = ftp.series_matrix_file_url(series.accession, platform.accession)
        probe_file = join(cache_dir, basename(url))
        if not can_be_used(probe_file):
            downloader.dl(url, probe_file)
        probe = pd.read_table(probe_file, comment=SOFT_COMMIT_CHAR, index_col=0)
        print_ocmir('probe_count', probe.shape[0], ocmir)
        print_ocmir('sample_count', probe.shape[1], ocmir)

        # 3. probe to gene
        gene = getattr(probe.groupby(mapping), aggregate_function)()
        print_ocmir('gene_count', gene.shape[0], ocmir)

        # 4. save to file
        clinical_file = clinical_file.format(accession=series.accession)
        expression_file = expression_file.format(accession=series.accession)
        clinical.to_csv(clinical_file, sep='\t', index=False)
        gene.to_csv(
            expression_file,
            sep='\t',
            index_label=platform.columns[gene_col-1].name if gene_col else 'gene'
        )
        print(f'Clinical file were saved to {clinical_file}.')
        print(f'Expression file were saved to {expression_file}.')
    except click.UsageError:
        raise
    except GeoAlchemyError as exc:
        logger.exception(exc)
        raise click.UsageError(str(exc))
    except Exception as exc:
        logger.exception(exc)
        raise click.UsageError('Unknown error occurred, refer to log file for details.')
