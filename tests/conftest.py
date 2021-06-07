# -*- coding: utf-8 -*-
import os
import json
from datetime import date

import pytest
from lxml import etree

import geo_alchemy
from geo_alchemy.utils import remove_namespace


@pytest.fixture
def basedir():
    return os.path.dirname(os.path.realpath(__file__))


@pytest.fixture
def platform_internal_data_file(basedir):
    return os.path.join(basedir, 'data', 'GPL570-internal-data.json')


@pytest.fixture
def platform_miniml_file(basedir):
    return os.path.join(basedir, 'data', 'GPL570.xml')


@pytest.fixture
def sample_miniml_file(basedir):
    return os.path.join(basedir, 'data', 'GSM1885279.xml')


@pytest.fixture
def series_miniml_file(basedir):
    return os.path.join(basedir, 'data', 'GSE73091.xml')


@pytest.fixture
def platform_miniml(platform_miniml_file):
    with open(platform_miniml_file, 'rb') as fp:
        return fp.read()


@pytest.fixture
def sample_miniml(sample_miniml_file):
    with open(sample_miniml_file, 'rb') as fp:
        return fp.read()


@pytest.fixture
def series_miniml(series_miniml_file):
    with open(series_miniml_file, 'rb') as fp:
        return fp.read()


@pytest.fixture
def organism():
    return geo_alchemy.Organism(
        taxid='9606',
        sciname='Homo sapiens'
    )


@pytest.fixture
def experiment_type_parser(series_miniml):
    element = remove_namespace(etree.fromstring(sample_miniml))
    return geo_alchemy.ExperimentTypeParser(
        element.xpath('/MINiML/Series/Type')[0]
    )


@pytest.fixture
def supplementary_data_item_parser(sample_miniml):
    element = remove_namespace(etree.fromstring(sample_miniml))
    return geo_alchemy.SupplementaryDataItemParser(
        element.xpath('/MINiML/Sample/Supplementary-Data')[0]
    )


@pytest.fixture
def organism_parser(sample_miniml):
    element = remove_namespace(etree.fromstring(sample_miniml))
    element = element.xpath('/MINiML/Sample/Channel/Organism')[0]
    return geo_alchemy.OrganismParser(element)


@pytest.fixture
def characteristic_parser(sample_miniml):
    element = remove_namespace(etree.fromstring(sample_miniml))
    element = element.xpath('/MINiML/Sample/Channel/Characteristics')[0]
    return geo_alchemy.CharacteristicParser(element)


@pytest.fixture
def channel_parser(sample_miniml):
    element = remove_namespace(etree.fromstring(sample_miniml))
    element = element.xpath('/MINiML/Sample/Channel')[0]
    return geo_alchemy.ChannelParser(element)


@pytest.fixture
def column_parser(sample_miniml):
    element = remove_namespace(etree.fromstring(sample_miniml))
    element = element.xpath('/MINiML/Sample/Data-Table/Column')[1]
    return geo_alchemy.ColumnParser(element)


@pytest.fixture
def platform_parser(platform_miniml):
    return geo_alchemy.PlatformParser.from_miniml(platform_miniml)


@pytest.fixture
def sample_parser(sample_miniml):
    return geo_alchemy.SampleParser.from_miniml(sample_miniml)


@pytest.fixture
def series_parser(series_miniml):
    return geo_alchemy.SeriesParser.from_miniml(series_miniml)


@pytest.fixture
def experiment_type():
    return geo_alchemy.ExperimentType(title='Expression profiling by array')


@pytest.fixture
def platform(platform_internal_data_file):
    title = '[HG-U133_Plus_2] Affymetrix Human Genome U133 Plus 2.0 Array'
    accession = 'GPL570'
    technology = 'in situ oligonucleotide'
    distribution = 'commercial'
    organisms = [
        geo_alchemy.Organism(
            taxid='9606',
            sciname='Homo sapiens'
        )
    ]
    manufacturer = 'Affymetrix'
    manufacturer_protocol = """see manufacturer's web site

Complete coverage of the Human Genome U133 Set plus 6,500 additional genes for analysis of over 47,000 transcripts
All probe sets represented on the GeneChip Human Genome U133 Set are identically replicated on the GeneChip Human Genome U133 Plus 2.0 Array. The sequences from which these probe sets were derived were selected from GenBank®, dbEST, and RefSeq. The sequence clusters were created from the UniGene database (Build 133, April 20, 2001) and then refined by analysis and comparison with a number of other publicly available databases, including the Washington University EST trace repository and the University of California, Santa Cruz Golden-Path human genome database (April 2001 release).
In addition, there are 9,921 new probe sets representing approximately 6,500 new genes. These gene sequences were selected from GenBank, dbEST, and RefSeq. Sequence clusters were created from the UniGene database (Build 159, January 25, 2003) and refined by analysis and comparison with a number of other publicly available databases, including the Washington University EST trace repository and the NCBI human genome assembly (Build 31)."""
    description = """Affymetrix submissions are typically submitted to GEO using the GEOarchive method described at http://www.ncbi.nlm.nih.gov/projects/geo/info/geo_affy.html

June 03, 2009: annotation table updated with netaffx build 28
June 06, 2012: annotation table updated with netaffx build 32
June 23, 2016: annotation table updated with netaffx build 35"""
    columns = [
        geo_alchemy.Column(
            position=1,
            name='ID',
            description='Affymetrix Probe Set ID'
        ),
        geo_alchemy.Column(
            position=2,
            name='GB_ACC',
            description='GenBank Accession Number'
        ),
        geo_alchemy.Column(
            position=3,
            name='SPOT_ID',
            description='identifies controls'
        ),
        geo_alchemy.Column(
            position=4,
            name='Species Scientific Name',
            description='The genus and species of the organism represented by the probe set.'
        ),
        geo_alchemy.Column(
            position=5,
            name='Annotation Date',
            description=(
                'The date that the annotations for this probe array were last updated. '
                'It will generally be earlier than the date when the annotations were posted '
                'on the Affymetrix web site.'
            )
        ),
        geo_alchemy.Column(
            position=6,
            name='Sequence Type',
            description=None
        ),
        geo_alchemy.Column(
            position=7,
            name='Sequence Source',
            description='The database from which the sequence used to design this probe set was taken.'
        ),
        geo_alchemy.Column(
            position=8,
            name='Target Description',
            description=None
        ),
        geo_alchemy.Column(
            position=9,
            name='Representative Public ID',
            description=(
                'The accession number of a representative sequence. '
                'Note that for consensus-based probe sets, the representative '
                'sequence is only one of several sequences (sequence sub-clusters) '
                'used to build the consensus sequence and it is not directly used to '
                'derive the probe sequences. The representative sequence is chosen during '
                'array design as a sequence that is best associated with the transcribed '
                'region being interrogated by the probe set. Refer to the "Sequence Source" '
                'field to determine the database used.'
            )
        ),
        geo_alchemy.Column(
            position=10,
            name='Gene Title',
            description='Title of Gene represented by the probe set.'
        ),
        geo_alchemy.Column(
            position=11,
            name='Gene Symbol',
            description='A gene symbol, when one is available (from UniGene).'
        ),
        geo_alchemy.Column(
            position=12,
            name='ENTREZ_GENE_ID',
            description='Entrez Gene Database UID'
        ),
        geo_alchemy.Column(
            position=13,
            name='RefSeq Transcript ID',
            description=(
                'References to multiple sequences in RefSeq. The field contains the ID '
                'and Description for each entry, and there can be multiple entries per '
                'ProbeSet.'
            )
        ),
        geo_alchemy.Column(
            position=14,
            name='Gene Ontology Biological Process',
            description=(
                'Gene Ontology Consortium Biological Process derived from LocusLink.  '
                'Each annotation consists of three parts: "Accession Number // Description '
                '// Evidence". The description corresponds directly to the GO ID. The evidence '
                'can be "direct", or "extended".'
            )
        ),
        geo_alchemy.Column(
            position=15,
            name='Gene Ontology Cellular Component',
            description=(
                'Gene Ontology Consortium Cellular Component derived from LocusLink.  '
                'Each annotation consists of three parts: "Accession Number // Description '
                '// Evidence". The description corresponds directly to the GO ID. The evidence '
                'can be "direct", or "extended".'
            )
        ),
        geo_alchemy.Column(
            position=16,
            name='Gene Ontology Molecular Function',
            description=(
                'Gene Ontology Consortium Molecular Function derived from LocusLink.  '
                'Each annotation consists of three parts: "Accession Number // Description '
                '// Evidence". The description corresponds directly to the GO ID. '
                'The evidence can be "direct", or "extended".'
            )
        ),
    ]
    with open(platform_internal_data_file) as fp:
        internal_data = json.load(fp)
    release_date = date(2003, 11, 7)
    last_update_date = date(2020, 12, 14)
    submission_date = date(2003, 11, 7)
    return geo_alchemy.Platform(
        title=title,
        accession=accession,
        technology=technology,
        distribution=distribution,
        organisms=organisms,
        manufacturer=manufacturer,
        manufacturer_protocol=manufacturer_protocol,
        description=description,
        columns=columns,
        internal_data=internal_data,
        release_date=release_date,
        last_update_date=last_update_date,
        submission_date=submission_date
    )


@pytest.fixture
def sample(platform):
    organisms = [
        geo_alchemy.Organism(
            taxid='9606',
            sciname='Homo sapiens'
        )
    ]
    characteristics = [
        geo_alchemy.Characteristic(
            tag='tumor type',
            value='primary'
        )
    ]
    extract_protocol = (
        "Isolation of RNA was performed using the Trizol "
        "method (Invitrogen) and was purified using RNeasy "
        "spin columns (Qiagen) according to the manufacturers' protocols."
    )
    label_protocol = (
        'Label protocol was carried out according to '
        'the Eukaryotic Target Preparation protocol in '
        'the Affymetrix technical manual (701021 Rev. 5) '
        'for Genechip Expression analysis (Affymetrix).'
    )
    channels = [
        geo_alchemy.Channel(
            position=1,
            source='LGSOC patient primary tumor',
            organisms=organisms,
            characteristics=characteristics,
            treatment_protocol=None,
            growth_protocol=None,
            molecule='total RNA',
            extract_protocol=extract_protocol,
            label='biotin',
            label_protocol=label_protocol
        )
    ]
    hybridization_protocol = (
        'Following fragmentation, 10 ug of cRNA were hybridized '
        'for 16 hr at 45C on Affymetrix Human Genome U133 Plus 2.0 Array. '
        'GeneChips were washed and stained in the Affymetrix Fluidics Station 400.'
    )
    scan_protocol = (
        'PICR scanner 3000'
    )
    description = 'Gene expression data from primary tumor cells.'
    data_processing = (
        'The data were analyzed with Microarray Suite version 5.0 '
        '(MAS 5.0) using Affymetrix default analysis settings and '
        'global scaling as normalization method. The trimmed mean '
        'target intensity of each array was arbitrarily set to 100.'
    )
    supplementary_data = [
        geo_alchemy.SupplementaryDataItem(
            type='CEL',
            url=(
                'ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM1885nnn/'
                'GSM1885279/suppl/GSM1885279_LGSOC-Patient01_primary_tumor_cells.CEL.gz'
            )
        )
    ]
    columns = [
        geo_alchemy.Column(
            position=1,
            name='ID_REF',
            description=None,
        ),
        geo_alchemy.Column(
            position=2,
            name='VALUE',
            description='MAS5.0 signal intensity',
        ),
        geo_alchemy.Column(
            position=3,
            name='ABS_CALL',
            description=None,
        ),
    ]
    internal_data = [
        ['1007_s_at', '2200.964', 'P'],
        ['1053_at', '221.1945', 'P'],
        ['117_at', '44.24419', 'A'],
        ['121_at', '617.3943', 'P'],
        ['1255_g_at', '41.6278', 'A'],
        ['1294_at', '362.6707', 'P'],
        ['1316_at', '242.5731', 'P'],
        ['1320_at', '88.42698', 'A'],
        ['1405_i_at', '124.5676', 'P'],
        ['1431_at', '92.14423', 'P'],
        ['1438_at', '32.28019', 'A'],
        ['1487_at', '481.5038', 'P'],
        ['1494_f_at', '94.68842', 'A'],
        ['1552256_a_at', '931.7369', 'P'],
        ['1552257_a_at', '1999.683', 'P'],
        ['1552258_at', '104.8575', 'P'],
        ['1552261_at', '35.51213', 'A'],
        ['1552263_at', '409.8742', 'P'],
        ['1552264_a_at', '341.7808', 'P'],
        ['1552266_at', '13.39048', 'A'],
    ]
    return geo_alchemy.Sample(
        title='LGSOC Patient1 primary tumor cells',
        accession='GSM1885279',
        type='RNA',
        channel_count=1,
        channels=channels,
        hybridization_protocol=hybridization_protocol,
        scan_protocol=scan_protocol,
        description=description,
        data_processing=data_processing,
        supplementary_data=supplementary_data,
        columns=columns,
        internal_data=internal_data,
        release_date=date(2017, 12, 19),
        last_update_date=date(2017, 12, 19),
        submission_date=date(2015, 9, 16),
        platform=platform
    )


@pytest.fixture
def series(platform, sample):
    title = (
        'Gene expression profile of tumor cells from primary tumors, ascites and '
        'metastases of low grade serous ovarian cancer patients'
    )
    accession = 'GSE73091'
    pmids = ['30710055']
    summary = """Differ from the aggressive nature of HGSOC (high grade serous ovarian cancer), LGSOC (low grade serous ovarian cancer) is characterized by an early age of disease onset, slow growth pattern, and poor response to chemotherapy. To understand more specifically the underlying gene profiling discrepancy that contributes to their behavior distinction, we performed parallel gene expression profiling in 9 magnetic sorted tumor cells samples from matched primary tumors, ascites and metastases of 3 LGSOC patients as in HGSOC. By comparing the expression data among primary tumor cells, ascitic tumor cells and metastasis tumor cells, we identified a set of differential expressed genes along LGSOC progression. Further study revealed that the gene phenotype perturbance along LGSOC progression was quite different from that of HGSOC patients.
We used microarrays to profile the expression of 9 matched tumor cells samples in order to identify molecular alteration between primary tumor cells, ascitic tumor cells and metastatic tumor cells in low grade serous ovarian cancer."""
    overall_design = (
        'Transcriptome profiling analyses were performed on 9 '
        'magnetical sorted epithelial tumor samples from matched '
        'primary tumors, ascites and metastases in low grade serous '
        'ovarian cancer patients, using the Affymetrix human genome '
        'U133 Plus 2.0 microarray.'
    )
    experiment_types = [
        geo_alchemy.ExperimentType(
            title='Expression profiling by array'
        )
    ]
    supplementary_data = [
        geo_alchemy.SupplementaryDataItem(
            type='TAR',
            url=(
                'ftp://ftp.ncbi.nlm.nih.gov/geo/series/'
                'GSE73nnn/GSE73091/suppl/GSE73091_RAW.tar'
            )
        )
    ]
    release_date = date(2017, 12, 19)
    last_update_date = date(2019, 3, 25)
    submission_date = date(2015, 9, 16)
    return geo_alchemy.Series(
        title=title,
        accession=accession,
        pmids=pmids,
        summary=summary,
        overall_design=overall_design,
        experiment_types=experiment_types,
        supplementary_data=supplementary_data,
        release_date=release_date,
        last_update_date=last_update_date,
        submission_date=submission_date,
        platforms=[platform],
        samples=[sample]
    )
