# -*- coding: utf-8 -*-
import codecs
import logging
import tempfile
import subprocess as sp
from os.path import join

import click
import pandas as pd

from ..geo import geo_router
from ..parsers import PlatformParser
from ..exceptions import GeoAlchemyError
from .helpers import (
    platform_accession_checker,
    check_blast_installation,
    Align,
)
from ..utils import (
    can_be_used,
    DEFAULT_REMAIN_SECONDS,
    http_downloader
)


logger = logging.getLogger('geo-alchemy')


@click.option(
    '-p', '--platform', 'accession',
    callback=platform_accession_checker,
    required=False,
    help='platform accession, if -a is not provided, this option should be provided.'
)
@click.option(
    '-a', '--anno-file',
    required=False,
    help='platform annotation file, if -p is not provided, this option should be provided.'
)
@click.option(
    '-s', '--seq', 'seq_col',
    required=True, type=click.IntRange(min=2),
    help='sequence column number in platform annotation file'
)
@click.option(
    '-d', '--db',
    required=True,
    help='BLAST db path'
)
@click.option(
    '-g', '--gencode', is_flag=True,
    help='BLAST db sequence download from gencode'
)
@click.option(
    '-me', '--max-evalue',
    type=click.FloatRange(min=0.0),
    default=1e-5, show_default=True,
    help='max evalue'
)
@click.option(
    '-ms', '--min-similarity',
    type=click.FloatRange(min=0.0, max=100.0),
    default=50.0, show_default=True,
    help='min similarity'
)
@click.option(
    '-mc', '--min-coverage',
    type=click.FloatRange(min=0.0, max=100.0),
    default=50.0, show_default=True,
    help='min coverage'
)
@click.option(
    '-o', '--outfile',
    default='{accession}_reanno.txt',
    show_default=True,
    type=click.Path(exists=False),
    help='output file'
)
@click.option(
    '--cache-dir',
    default='.',
    show_default=True,
    type=click.Path(exists=True),
    help='cache directory, when file existed in cache directory, network downloading will be omitted.'
)
def reanno(
    accession, anno_file, seq_col, db, gencode,
    max_evalue, min_similarity, min_coverage, outfile, cache_dir
):
    """
    Platform probe reannotation, prerequisites:
        1. NCBI BLAST must be installed.
        2. BLAST Index must be generated.
    """
    try:
        # 1. check BLAST installation
        check_blast_installation()

        # 2. get platform metadata
        seqs = None
        if anno_file:
            anno = pd.read_table(anno_file, index_col=0, comment='#')
            if seq_col > (anno.shape[1] + 1):
                raise click.UsageError(f'Invalid sequence column number {seq_col}')
            seqs = anno.iloc[:, seq_col-2].dropna().to_dict()
            logger.warning(f'%s NAs removed in annotation file {anno_file}.', anno.shape[0]-len(seqs))
        if (seqs is None) and accession:
            platform_file = join(cache_dir, f'{accession}.xml')
            if not can_be_used(platform_file, DEFAULT_REMAIN_SECONDS):
                http_downloader.dl(
                    geo_router.platform_detail(accession, view='full'),
                    outfile=platform_file
                )
            platform = PlatformParser.from_miniml_file(platform_file).parse()
            if seq_col > len(platform.columns):
                raise click.UsageError(f'Invalid sequence column number {seq_col}')
            seqs = {}
            seq_col -= 1
            na_count = 0
            for i, row in enumerate(platform.internal_data):
                if (seq_col > len(row)) or (not row[seq_col]):
                    na_count += 1
                    continue
                seqs[row[0]] = row[seq_col]
            logger.warning(f'{na_count} NAs removed.')
        if seqs is None:
            raise click.UsageError('Either -p or -a should be provided.')

        with tempfile.TemporaryDirectory() as tempdir:
            # 3. extract sequence
            seq_file = join(tempdir, 'seq.fa')
            with codecs.open(seq_file, 'w', encoding='utf-8') as fp:
                for sid, seq in seqs.items():
                    fp.write(f'>{sid}\n{seq}\n')

            # 4. alignment
            align_file = join(tempdir, 'align.txt')
            cmd = [
                'blastn',
                '-query', seq_file,
                '-db', db,
                '-max_target_seqs', '1',
                '-out', align_file,
                '-outfmt', '6 qseqid sseqid evalue pident qcovhsp'
            ]
            msg = 'running command: %s' % ' '.join(cmd)
            print(msg)
            logger.info(msg)
            proc = sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
            logger.info('stdout: ')
            logger.info(proc.stdout.decode('utf-8'))
            logger.info('stderr: ')
            logger.info(proc.stderr.decode('utf-8'))

            # 5. reanno
            aligns = Align.parse_file(align_file)
            aligns = [align for align in aligns if align.check(
                evalue=max_evalue,
                pident=min_similarity,
                qcovhsp=min_coverage
            )]

        # 5. save to file
        outfile = outfile.format(accession=accession) if accession else 'reanno.txt'
        with codecs.open(outfile, 'w', encoding='utf-8') as fp:
            fp.write('probe_id\tgene\n')
            for align in aligns:
                if gencode:
                    sseqid = align.sseqid.split('|')[5]
                else:
                    sseqid = align.sseqid
                fp.write(f'{align.qseqid}\t{sseqid}\n')
        print(f'Reannotation result were saved to file {outfile}')
    except click.UsageError:
        raise
    except GeoAlchemyError as exc:
        logger.exception(exc)
        raise click.UsageError(str(exc))
    except Exception as exc:
        logger.exception(exc)
        raise click.UsageError('Unknown error occurred, refer to log file for details.')
