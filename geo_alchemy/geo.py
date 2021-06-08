# -*- coding: utf-8 -*-
import os
import logging
from collections import OrderedDict
from urllib.parse import urlencode

from .exceptions import GeoAlchemyError
from .utils import (
    can_be_used,
    DEFAULT_RETRIES,
    DEFAULT_REMAIN_SECONDS,
    HttpDownloader,
    AsperaDownloader,
    DELIMITER,
)


logger = logging.getLogger('geo-alchemy')


class GeoRouter(object):
    base_list_url = 'https://www.ncbi.nlm.nih.gov/geo/browse'
    base_detail_url = 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi'
    base_ftp_url = 'ftp://ftp.ncbi.nlm.nih.gov'
    base_aspera_url = 'anonftp@ftp.ncbi.nlm.nih.gov'

    @staticmethod
    def _check_platform_accession(accession):
        if accession[: 3] != 'GPL':
            raise GeoAlchemyError(f"accession {accession} don't start with GPL")

    @staticmethod
    def _check_sample_accession(accession):
        if accession[: 3] != 'GSM':
            raise GeoAlchemyError(f"accession {accession} don't start with GSM")

    @staticmethod
    def _check_series_accession(accession):
        if accession[: 3] != 'GSE':
            raise GeoAlchemyError(f"accession {accession} don't start with GSE")

    def _list(self, view, zsort='date', display=20, page=1):
        query_params = urlencode({
            'view': view, 'zsort': zsort,
            'display': display, 'page': page
        })
        return f'{self.base_list_url}?{query_params}'

    def _detail(self, accession, targ='self', form='xml', view='quick'):
        query_params = urlencode({
            'acc': accession, 'targ': targ, 'form': form, 'view': view
        })
        return f'{self.base_detail_url}?{query_params}'

    def series_list(self, zsort='date', display=20, page=1):
        return self._list('series', zsort, display, page)

    def sample_list(self, zsort='date', display=20, page=1):
        return self._list('samples', zsort, display, page)

    def platform_list(self, zsort='date', display=20, page=1):
        return self._list('platforms', zsort, display, page)

    def series_detail(self, accession, targ='all', form='xml', view='quick'):
        self._check_series_accession(accession)
        return self._detail(accession, targ, form, view)

    def sample_detail(self, accession, targ='self', form='xml', view='quick'):
        self._check_sample_accession(accession)
        return self._detail(accession, targ, form, view)

    def platform_detail(self, accession, targ='self', form='xml', view='quick'):
        self._check_platform_accession(accession)
        return self._detail(accession, targ, form, view)

    def series_matrix_file_uri(self, accession):
        self._check_series_accession(accession)
        return ('/geo/series/{prefix}nnn/{accession}'
                '/matrix/{accession}_series_matrix.txt.gz').format(
            prefix=accession[: -3],
            accession=accession
        )

    def series_matrix_file_url(self, accession):
        self._check_series_accession(accession)
        return '{base_ftp_url}{uri}'.format(
            base_ftp_url=self.base_ftp_url,
            uri=self.series_matrix_file_uri(accession)
        )

    def series_matrix_file_aspera_url(self, accession):
        self._check_series_accession(accession)
        return '{base_aspera_url}{uri}'.format(
            base_aspera_url=self.base_aspera_url,
            uri=self.series_matrix_file_uri(accession)
        )

    def series_matrix_file_uri_multiple_platforms(self, series_accession, platform_accession):
        self._check_series_accession(series_accession)
        self._check_platform_accession(platform_accession)
        return (
            '/geo/series/{prefix}nnn/{accession}/matrix/'
            '{series_accession}-{platform_accession}_series_matrix.txt.gz'
        ).format(
            prefix=series_accession[: -3],
            seris_accession=series_accession,
            platform_accession=platform_accession
        )

    def series_matrix_file_url_multiple_platforms(self, series_accession, platform_accession):
        self._check_series_accession(series_accession)
        self._check_platform_accession(platform_accession)
        return '{base_ftp_url}{uri}'.format(
            base_ftp_url=self.base_ftp_url,
            uri=self.series_matrix_file_uri_multiple_platforms(
                series_accession, platform_accession
            )
        )

    def series_matrix_file_aspera_url_multiple_platforms(
            self, series_accession, platform_accession
    ):
        self._check_series_accession(series_accession)
        self._check_platform_accession(platform_accession)
        return '{base_aspera_url}{uri}'.format(
            base_aspera_url=self.base_aspera_url,
            uri=self.series_matrix_file_uri_multiple_platforms(
                series_accession, platform_accession
            )
        )


geo_router = GeoRouter()


class SupplementaryDataItem(object):
    def __init__(self, type, url):
        self.type = type
        self.url = url

    def __repr__(self):
        return f'SupplementaryDataItem<{self.url}({self.type})>'

    def __eq__(self, other):
        if not isinstance(other, SupplementaryDataItem):
            raise NotImplemented
        return (self.type == other.type) and (self.url == other.url)

    def to_dict(self):
        return {
            'type': self.type,
            'url': self.url
        }


class Organism(object):
    def __init__(self, taxid, sciname):
        """
        Args:
            taxid: NCBI taxonomy ID
            sciname: scientific name
        """
        self.taxid = taxid
        self.sciname = sciname

    def __repr__(self):
        return f'Organism<{self.taxid}: {self.sciname}>'

    def __eq__(self, other):
        if not isinstance(other, Organism):
            raise NotImplemented
        return (self.taxid == other.taxid) and (self.sciname == other.sciname)

    def to_dict(self):
        return {
            'taxid': self.taxid,
            'sciname': self.sciname
        }


class ExperimentType(object):
    def __init__(self, title):
        """
        Args:
            title: title of experiment type
        """
        self.title = title

    def __eq__(self, other):
        if not isinstance(other, ExperimentType):
            raise NotImplemented
        return self.title == other.title

    def __repr__(self):
        return f'ExperimentType<{self.title}>'

    def to_dict(self):
        return {
            'title': self.title
        }


class Column(object):
    def __init__(self, position, name, description):
        """
        Args:
            position: eg, 11
            name: eg, Gene Symbol
            description: eg, A gene symbol, when one is available (from UniGene).
        """
        self.position = position
        self.name = name
        self.description = description

    def __repr__(self):
        return f'Column<{self.name}>'

    def __eq__(self, other):
        if not isinstance(other, Column):
            raise NotImplemented
        return (self.position == other.position) and (
                self.name == other.name) and (self.description == other.description)

    def to_dict(self):
        return {
            'position': self.position,
            'name': self.name,
            'description': self.description
        }


class Platform(object):
    def __init__(
        self, accession, title=None, technology=None,
        distribution=None, organisms=None, manufacturer=None,
        manufacturer_protocol=None, description=None,
        columns=None, internal_data=None, release_date=None,
        last_update_date=None, submission_date=None
    ):
        """
        Args:
            accession: eg, GPL570
            title: eg, [HG-U133_Plus_2] Affymetrix Human Genome U133 Plus 2.0 Array
            technology: eg, in situ oligonucleotide
            distribution: eg, commercial
            organisms: correspond organisms, list of Organism objects
            manufacturer: eg, Affymetrix
            manufacturer_protocol:
            description: platform description text
            columns: platform columns, list of PlatformColumn objects
            internal_data: platform internal data, list of dicts
            release_date: release date
            last_update_date: last update date
            submission_date: submission date
        """
        self.accession = accession
        self.title = title
        self.technology = technology
        self.distribution = distribution
        self.organisms = organisms if organisms else []
        self.manufacturer = manufacturer
        self.manufacturer_protocol = manufacturer_protocol
        self.description = description
        self.columns = columns if columns else []
        self.internal_data = internal_data
        self.release_date = release_date
        self.last_update_date = last_update_date
        self.submission_date = submission_date

    def __repr__(self):
        return f'Platform<{self.accession}>'

    def __eq__(self, other):
        if not isinstance(other, Platform):
            raise NotImplemented
        return (self.accession == other.accession) and (self.title == other.title) and (
                self.technology == other.technology) and (self.distribution == other.distribution) and (
                       self.organisms == other.organisms) and (self.manufacturer == other.manufacturer) and (
                       self.manufacturer_protocol == other.manufacturer_protocol) and (
                       self.description == other.description) and (self.columns == other.columns) and (
                       self.internal_data == other.internal_data) and (self.release_date == other.release_date) and (
                       self.last_update_date == other.last_update_date) and (self.submission_date == other.submission_date)

    def to_dict(self):
        return {
            'title': self.title,
            'accession': self.accession,
            'technology': self.technology,
            'distribution': self.distribution,
            'organisms': [organism.to_dict() for organism in self.organisms],
            'manufacturer': self.manufacturer,
            'manufacturer_protocol': self.manufacturer_protocol,
            'description': self.description,
            'columns': [column.to_dict() for column in self.columns],
            'internal_data': self.internal_data,
            'release_date': self.release_date.strftime(
                '%Y-%m-%d'
            ) if self.release_date else None,
            'last_update_date': self.last_update_date.strftime(
                '%Y-%m-%d'
            ) if self.last_update_date else None,
            'submission_date': self.submission_date.strftime(
                '%Y-%m-%d'
            ) if self.submission_date else None,
        }

    def get_probe_gene_mapping(self, gene_col):
        if not (self.columns and self.internal_data):
            raise GeoAlchemyError(f'malformed platform {self.accession}')
        if len(self.columns) != len(self.internal_data[0]):
            raise GeoAlchemyError(f'malformed platform {self.accession}')
        col_num = len(self.columns)
        if (gene_col+1) >= col_num:
            raise GeoAlchemyError(f'gene column {gene_col+1}, but only {col_num} totally.')
        mapping = OrderedDict()
        for i, row in enumerate(self.internal_data):
            row_col_num = len(row)
            if row_col_num != col_num:
                logger.warning(
                    f'malformed platform annotation row {i}, only {row_col_num} columns, '
                    f'should have {col_num} columns normally.'
                )
                continue
            mapping[row[0]] = row[gene_col]
        return mapping

    @property
    def is_malformed(self):
        return self.title is None


class Characteristic(object):
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value

    def __repr__(self):
        return f'Characteristic<{self.tag}>'

    def __eq__(self, other):
        if not isinstance(other, Characteristic):
            raise NotImplemented
        return (self.tag == other.tag) and (self.value == other.value)

    def to_dict(self):
        return {
            'tag': self.tag,
            'value': self.value
        }


class Channel(object):
    def __init__(
        self, position, source, organisms,
        characteristics, treatment_protocol,
        growth_protocol, molecule, extract_protocol,
        label, label_protocol
    ):
        """
        Args:
            position: channel position, eg, 1
            source: eg, pooled hepatopancreas samples from 9 P.
                        monodon broodstock pre-treatment with stage 1 ovaries
            organisms: correspond organisms, list of Organism objects
            characteristics: list of dicts
            treatment_protocol:
            growth_protocol:
            molecule: eg, total RNA
            extract_protocol:
            label: eg, Cy3
            label_protocol:
        """
        self.position = position
        self.source = source
        self.organisms = organisms
        self.characteristics = characteristics
        self.treatment_protocol = treatment_protocol
        self.growth_protocol = growth_protocol
        self.molecule = molecule
        self.extract_protocol = extract_protocol
        self.label = label
        self.label_protocol = label_protocol

    def __repr__(self):
        return f'Channel<{self.position}>'

    def __eq__(self, other):
        if not isinstance(other, Channel):
            raise NotImplemented
        return (self.position == other.position) and (self.source == other.source) and (
                self.organisms == other.organisms) and (self.characteristics == other.characteristics) and (
                       self.treatment_protocol == other.treatment_protocol) and (
                       self.growth_protocol == other.growth_protocol) and (self.molecule == other.molecule) and (
                       self.extract_protocol == other.extract_protocol) and (self.label == other.label) and (
                       self.label_protocol == other.label_protocol)

    def to_dict(self):
        return {
            'position': self.position,
            'source': self.source,
            'organisms': [organism.to_dict() for organism in self.organisms],
            'characteristics': [
                characteristic.to_dict() for characteristic in self.characteristics
            ],
            'treatment_protocol': self.treatment_protocol,
            'growth_protocol': self.growth_protocol,
            'molecule': self.molecule,
            'extract_protocol': self.extract_protocol,
            'label': self.label,
            'label_protocol': self.label_protocol
        }


class Sample(object):

    def __init__(
        self, accession, title=None, type=None,
        channel_count=None, channels=None,
        hybridization_protocol=None, scan_protocol=None,
        description=None, data_processing=None, supplementary_data=None,
        columns=None, internal_data=None, release_date=None,
        last_update_date=None, submission_date=None, platform=None
    ):
        self.accession = accession
        self.title = title
        self.type = type
        self.channel_count = channel_count
        self.channels = channels if channels else []
        self.hybridization_protocol = hybridization_protocol
        self.scan_protocol = scan_protocol
        self.description = description
        self.data_processing = data_processing
        self.supplementary_data = supplementary_data if supplementary_data else []
        self.columns = columns if columns else []
        self.internal_data = internal_data
        self.release_date = release_date
        self.last_update_date = last_update_date
        self.submission_date = submission_date
        self.platform = platform

    def __repr__(self):
        return f'Sample<{self.accession}>'

    def __eq__(self, other):
        if not isinstance(other, Sample):
            raise NotImplemented
        return (self.accession == other.accession) and (self.title == other.title) and (
                self.type == other.type) and (self.channel_count == other.channel_count) and (
                       self.channels == other.channels) and (self.hybridization_protocol == other.hybridization_protocol) and (
                       self.scan_protocol == other.scan_protocol) and (self.description == other.description) and (
                       self.data_processing == other.data_processing) and (
                       self.supplementary_data == other.supplementary_data) and (self.columns == other.columns) and (
                       self.internal_data == other.internal_data) and (self.release_date == other.release_date) and (
                       self.last_update_date == other.last_update_date) and (self.submission_date == other.submission_date) and (
                       self.platform == other.platform)

    def to_dict(self):
        return {
            'title': self.title,
            'accession': self.accession,
            'type': self.type,
            'channel_count': self.channel_count,
            'channels': [channel.to_dict() for channel in self.channels],
            'hybridization_protocol': self.hybridization_protocol,
            'scan_protocol': self.scan_protocol,
            'description': self.description,
            'data_processing': self.data_processing,
            'supplementary_data': [
                supplementary_data_item.to_dict() for supplementary_data_item in self.supplementary_data
            ],
            'columns': [column.to_dict() for column in self.columns],
            'internal_data': self.internal_data,
            'release_date': self.release_date.strftime(
                '%Y-%m-%d'
            ) if self.release_date else None,
            'last_update_date': self.last_update_date.strftime(
                '%Y-%m-%d'
            ) if self.last_update_date else None,
            'submission_date': self.submission_date.strftime(
                '%Y-%m-%d'
            ) if self.submission_date else None,
            'platform': self.platform.to_dict() if self.platform else None
        }

    @property
    def organisms(self):
        cache = set()
        organisms = []
        for channel in self.channels:
            if not channel.organisms:
                continue
            for organism in channel.organisms:
                if organism.taxid in cache:
                    continue
                organisms.append(organism)
                cache.add(organism.taxid)
        return organisms

    @property
    def clinical(self):
        data = {
            'accession': self.accession,
            'title': self.title,
            'platform': self.platform.accession if self.platform else None,
        }
        if self.channels is None:
            return data
        if len(self.channels) == 1:
            data['source'] = self.channels[0].source
            scinames = OrderedDict()
            for organism in self.channels[0].organisms:
                if organism.sciname not in scinames:
                    scinames[organism.sciname] = None
            data['organism'] = DELIMITER.join(scinames.keys())
            tags = {}
            for ch in self.channels[0].characteristics:
                if ch.tag in tags:
                    if tags[ch.tag] == 1:
                        data[f'{ch.tag}_1'] = data[ch.tag]
                        del data[ch.tag]
                    tags[ch.tag] += 1
                    data[f'{ch.tag}_{tags[ch.tag]}'] = ch.value
                else:
                    tags[ch.tag] = 1
                    data[ch.tag] = ch.value
            data['molecule'] = self.channels[0].molecule
        else:
            if self.channels[0].source == self.channels[1].source:
                source = self.channels[0].source
            else:
                source = DELIMITER.join([
                    self.channels[0].source, self.channels[1].source
                ])
            data['source'] = source
            scinames = OrderedDict()
            for organism in self.channels[0].organisms:
                if organism.sciname not in scinames:
                    scinames[organism.sciname] = None
            for organism in self.channels[1].organisms:
                if organism.sciname not in scinames:
                    scinames[organism.sciname] = None
            data['organism'] = DELIMITER.join(scinames.keys())
            tags = {}
            for ch in self.channels[0].characteristics:
                tag = f'ch1_{ch.tag}'
                value = ch.value
                if tag in tags:
                    if tags[tag] == 1:
                        data[f'{tag}_1'] = data[tag]
                        del data[ch.tag]
                    tags[tag] += 1
                    data[f'{tag}_{tags[tag]}'] = value
                else:
                    tags[tag] = 1
                    data[tag] = value
            for ch in self.channels[1].characteristics:
                tag = f'ch2_{ch.tag}'
                value = ch.value
                if tag in tags:
                    if tags[tag] == 1:
                        data[f'{tag}_1'] = data[tag]
                        del data[ch.tag]
                    tags[tag] += 1
                    data[f'{tag}_{tags[tag]}'] = value
                else:
                    tags[tag] = 1
                    data[tag] = value
            if self.channels[0].molecule == self.channels[1].molecule:
                molecule = self.channels[0].molecule
            else:
                molecule = DELIMITER.join([
                    self.channels[0].molecule,
                    self.channels[1].molecule,
                ])
            data['molecule'] = molecule
        return data

    @property
    def is_malformed(self):
        return self.title is None


class Series(object):
    def __init__(
        self, accession, title=None, pmids=None, summary=None,
        overall_design=None, experiment_types=None, supplementary_data=None,
        release_date=None, last_update_date=None, submission_date=None, samples=None
    ):
        self.accession = accession
        self.title = title
        self.pmids = pmids if pmids else []
        self.summary = summary
        self.overall_design = overall_design
        self.experiment_types = experiment_types if experiment_types else []
        self.supplementary_data = supplementary_data if supplementary_data else []
        self.release_date = release_date
        self.last_update_date = last_update_date
        self.submission_date = submission_date
        self.samples = samples if samples else []

    def __repr__(self):
        return f'Series<{self.accession}>'

    def __eq__(self, other):
        if not isinstance(other, Series):
            raise NotImplemented
        return (self.title == other.title) and (self.accession == other.accession) and (
                self.pmids == other.pmids) and (self.summary == other.summary) and (
                self.overall_design == other.overall_design) and (self.experiment_types == other.experiment_types) and (
                self.supplementary_data == other.supplementary_data) and (self.release_date == other.release_date) and (
                self.last_update_date == other.last_update_date) and (self.submission_date == other.submission_date) and (
                self.samples == other.samples)

    def to_dict(self):
        return {
            'accession': self.accession,
            'title': self.title,
            'pmids': self.pmids,
            'summary': self.summary,
            'overall_design': self.overall_design,
            'experiment_types': [
                experiment_type.to_dict() for experiment_type in self.experiment_types
            ],
            'supplementary_data': [
                supplementary_data_item.to_dict(
                ) for supplementary_data_item in self.supplementary_data
            ],
            'release_date': self.release_date.strftime('%Y-%m-%d') if self.release_date else None,
            'last_update_date': self.last_update_date.strftime('%Y-%m-%d') if self.last_update_date else None,
            'submission_date': self.submission_date.strftime('%Y-%m-%d') if self.submission_date else None,
            'samples': [sample.to_dict() for sample in self.samples],
        }

    @property
    def platforms(self):
        cache = set()
        platforms = []
        for sample in self.samples:
            if not sample.platform:
                continue
            if sample.platform.accession in cache:
                continue
            platforms.append(sample.platform)
            cache.add(sample.platform.accession)
        return platforms

    def set_samples(self, samples):
        self.samples = samples

    def add_sample(self, sample):
        self.samples.append(sample)

    @property
    def sample_count(self):
        return len(self.samples)

    @property
    def organisms(self):
        cache = set()
        organisms = []
        for sample in self.samples:
            for organism in sample.organisms:
                if organism.taxid in cache:
                    continue
                organisms.append(organism)
                cache.add(organism.taxid)
        return organisms

    def dl_series_matrix(self, platform=None, outdir='.'):
        """
        download series matrix text file
        Args:
            platform: platform accession or platform object, when
                      series has multiple platforms, this argument
                      must provide.
            outdir: series matrix text file saved directory
        Returns:
            downloaded series matrix text file path
        """
        available_platforms = self.platforms
        if len(available_platforms) == 0:
            raise GeoAlchemyError(f'malformed series {self.accession}')
        elif len(available_platforms) == 1:
            platform = available_platforms[0]
        else:
            if platform is None:
                raise GeoAlchemyError(
                    'this series has multiple platforms, '
                    'platform accession or platform object must be provided.'
                )
            if isinstance(platform, str):
                for available_platform in available_platforms:
                    if available_platform.accession == platform:
                        platform = available_platform
        if not isinstance(platform, Platform):
            raise GeoAlchemyError('Invalid platform %s' % str(platform))
        if len(available_platforms) == 1:
            url = geo_router.series_matrix_file_url(self.accession)
            aspera_url = geo_router.series_matrix_file_aspera_url(self.accession)
        else:
            url = geo_router.series_matrix_file_url_multiple_platforms(
                self.accession, platform.accession
            )
            aspera_url = geo_router.series_matrix_file_aspera_url_multiple_platforms(
                    self.accession, platform.accession
            )
        fn = os.path.basename(url)
        file = os.path.join(outdir, fn)
        if can_be_used(file, DEFAULT_REMAIN_SECONDS):
            return file
        downloader = AsperaDownloader(DEFAULT_RETRIES)
        if downloader.check():
            return downloader.dl(aspera_url, outfile=file)
        else:
            downloader = HttpDownloader(DEFAULT_RETRIES)
            return downloader.dl(url, outfile=file)

    @property
    def clinical(self):
        return [samples.clinical for samples in self.samples]

    def get_platform_clinical(self, platform):
        clinical = []
        for sample in self.samples:
            if sample.platform.accession == platform.accession:
                clinical.append(sample.clinical)
        return clinical

    @property
    def is_malformed(self):
        return self.title is None
