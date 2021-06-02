# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import click
from lxml import etree


logger = logging.getLogger('geo-alchemy')


class GeoAlchemyError(Exception):
    """ancestor error of geo-alchemy"""


def remove_namespace(tree):
    """
    remove namespace of a tree

    Args:
        tree: lxml.etree._ElementTree object
    Returns:
        lxml.etree._Element without namespace
    """
    for element in tree.iter():
        element.tag = etree.QName(element).localname
    etree.cleanup_namespaces(tree)
    return tree


def date_from_geo_string(geo_string):
    """get date from GEO release date、last update date、submission date string"""
    return datetime.strptime(geo_string, '%Y-%m-%d').date()


def validate_series_accession(ctx, param, value):
    if (len(value) <= 3) or (value[: 3] != 'GSE'):
        raise click.UsageError(f"Series accession {value} don't start with GSE")
    return value


class GeoRouter(object):
    base_list_url = 'https://www.ncbi.nlm.nih.gov/geo/browse'
    base_detail_url = 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi'

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

    def series_detail(self, accession, targ='self', form='xml', view='quick'):
        if accession[: 3] != 'GSE':
            raise GeoAlchemyError(f"accession {accession} don't start with GSE")
        return self._detail(accession, targ, form, view)

    def sample_detail(self, accession, targ='self', form='xml', view='quick'):
        if accession[: 3] != 'GSM':
            raise GeoAlchemyError(f"accession {accession} don't start with GSM")
        return self._detail(accession, targ, form, view)

    def platform_detail(self, accession, targ='self', form='xml', view='quick'):
        if accession[: 3] != 'GPL':
            raise GeoAlchemyError(f"accession {accession} don't start with GPL")
        return self._detail(accession, targ, form, view)


geo_router = GeoRouter()


class BaseParser(object):
    def __init__(self, element, rm_ns=True):
        if rm_ns:
            element = remove_namespace(element)
        self.element = element

    @classmethod
    def from_miniml(cls, miniml):
        element = etree.fromstring(miniml)
        return cls(element, rm_ns=True)

    @classmethod
    def from_miniml_file(cls, miniml_file):
        with open(miniml_file, 'rb') as fp:
            return cls.from_miniml(fp.read())

    @classmethod
    def from_accession(cls, accession):
        raise NotImplemented

    def parse(self):
        raise NotImplemented


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


class SupplementaryDataItemParser(BaseParser):
    def parse_type(self):
        return self.element.get('type')

    def parse_url(self):
        return self.element.text.strip()

    def parse(self):
        type = self.parse_type()
        url = self.parse_url()
        return SupplementaryDataItem(
            type=type,
            url=url
        )

    @classmethod
    def parse_dict(cls, data):
        return SupplementaryDataItem(
            type=data['type'],
            url=data['url']
        )


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


class OrganismParser(BaseParser):
    def parse_taxid(self):
        return self.element.get('taxid')

    def parse_sciname(self):
        return self.element.text

    def parse(self):
        taxid = self.parse_taxid()
        sciname = self.parse_sciname()
        return Organism(
            taxid=taxid,
            sciname=sciname
        )

    @classmethod
    def parse_dict(cls, data):
        return Organism(
            taxid=data['taxid'],
            sciname=data['sciname']
        )


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


class ExperimentTypeParser(BaseParser):
    def parse_title(self):
        return self.element.text.strip()

    def parse(self):
        title = self.parse_title()
        return ExperimentType(title=title)

    @classmethod
    def parse_dict(cls, data):
        return ExperimentType(
            title=data['title']
        )


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


class ColumnParser(BaseParser):
    def parse_position(self):
        return int(self.element.get('position'))

    def parse_name(self):
        return self.element.xpath('./Name/text()')[0].strip()

    def parse_description(self):
        description = self.element.xpath('./Description/text()')
        if description:
            return description[0].strip()
        return None

    def parse(self):
        position = self.parse_position()
        name = self.parse_name()
        description = self.parse_description()
        return Column(
            position=position,
            name=name,
            description=description
        )

    @classmethod
    def parse_dict(cls, data):
        return Column(
            position=data['position'],
            name=data['name'],
            description=data['description']
        )


class Platform(object):
    def __init__(
        self, title, accession, technology,
        distribution, organisms, manufacturer,
        manufacturer_protocol, description,
        columns, internal_data, release_date,
        last_update_date, submission_date
    ):
        """
        Args:
            title: eg, [HG-U133_Plus_2] Affymetrix Human Genome U133 Plus 2.0 Array
            accession: eg, GPL570
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
        self.title = title
        self.accession = accession
        self.technology = technology
        self.distribution = distribution
        self.organisms = organisms
        self.manufacturer = manufacturer
        self.manufacturer_protocol = manufacturer_protocol
        self.description = description
        self.columns = columns
        self.internal_data = internal_data
        self.release_date = release_date
        self.last_update_date = last_update_date
        self.submission_date = submission_date

    def __repr__(self):
        return f'Platform<{self.accession}>'

    def __eq__(self, other):
        if not isinstance(other, Platform):
            raise NotImplemented
        return (self.title == other.title) and (self.accession == other.accession) and (
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
            'release_date': self.release_date.strftime('%Y-%m-%d'),
            'last_update_date': self.last_update_date.strftime('%Y-%m-%d'),
            'submission_date': self.submission_date.strftime('%Y-%m-%d'),
        }


class PlatformParser(BaseParser):
    _platforms = {}

    @classmethod
    def from_accession(cls, accession):
        url = geo_router.platform_detail(
            accession=accession,
            targ='self',
            form='xml',
            view='quick'
        )
        logger.info(f'accessing {url}.')
        req = urlopen(url)
        miniml = req.read()
        return cls.from_miniml(miniml)

    def parse_title(self):
        return self.element.xpath('/MINiML/Platform/Title/text()')[0]

    def parse_accession(self):
        return self.element.xpath('/MINiML/Platform/Accession/text()')[0]

    def parse_technology(self):
        return self.element.xpath('/MINiML/Platform/Technology/text()')[0]

    def parse_distribution(self):
        return self.element.xpath('/MINiML/Platform/Distribution/text()')[0]

    def parse_organisms(self):
        organisms = []
        for element in self.element.xpath('/MINiML/Platform/Organism'):
            parser = OrganismParser(element)
            organisms.append(parser.parse())
        return organisms

    def parse_manufacturer(self):
        manufacturer = self.element.xpath('/MINiML/Platform/Manufacturer/text()')
        if manufacturer:
            return manufacturer[0].strip()
        return None

    def parse_manufacturer_protocol(self):
        manufacturer_protocol = self.element.xpath(
            '/MINiML/Platform/Manufacture-Protocol/text()'
        )
        if manufacturer_protocol:
            return manufacturer_protocol[0].strip()
        return None

    def parse_description(self):
        description = self.element.xpath(
            '/MINiML/Platform/Description/text()'
        )
        if description:
            return description[0].strip()
        return None

    def parse_columns(self):
        columns = []
        for element in self.element.xpath('/MINiML/Platform/Data-Table/Column'):
            parser = ColumnParser(element)
            columns.append(parser.parse())
        return columns

    def parse_internal_data(self):
        internal_data_text = self.element.xpath(
            '/MINiML/Platform/Data-Table/Internal-Data/text()'
        )
        if internal_data_text:
            internal_data_text = internal_data_text[0].strip()
            internal_data = []
            for line in internal_data_text.split('\n'):
                if not line:
                    continue
                internal_data.append(line.split('\t'))
            return internal_data
        return None

    def parse_release_date(self):
        return date_from_geo_string(
            self.element.xpath('/MINiML/Platform/Status/Release-Date/text()')[0]
        )

    def parse_last_update_date(self):
        return date_from_geo_string(
            self.element.xpath('/MINiML/Platform/Status/Last-Update-Date/text()')[0]
        )

    def parse_submission_date(self):
        return date_from_geo_string(
            self.element.xpath('/MINiML/Platform/Status/Submission-Date/text()')[0]
        )

    @classmethod
    def add_platform(cls, platform):
        cls._platforms[platform.accession] = platform

    @classmethod
    def get_platform(cls, accession):
        return cls._platforms.get(accession, None)

    def parse(self):
        accession = self.parse_accession()
        title = self.parse_title()
        technology = self.parse_technology()
        distribution = self.parse_distribution()
        organisms = self.parse_organisms()
        manufacturer = self.parse_manufacturer()
        manufacturer_protocol = self.parse_manufacturer_protocol()
        description = self.parse_description()
        columns = self.parse_columns()
        internal_data = self.parse_internal_data()
        release_date = self.parse_release_date()
        last_update_date = self.parse_last_update_date()
        submission_date = self.parse_submission_date()
        platform = Platform(
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
        self._platforms[accession] = platform
        return platform

    @classmethod
    def parse_dict(cls, data):
        organisms = [
            OrganismParser.parse_dict(
                organism_data
            ) for organism_data in data['organisms']
        ]
        columns = [
            ColumnParser.parse_dict(
                column_data
            ) for column_data in data['columns']
        ]
        platform = Platform(
            title=data['title'],
            accession=data['accession'],
            technology=data['technology'],
            distribution=data['distribution'],
            organisms=organisms,
            manufacturer=data['manufacturer'],
            manufacturer_protocol=data['manufacturer_protocol'],
            description=data['description'],
            columns=columns,
            internal_data=data['internal_data'],
            release_date=date_from_geo_string(data['release_date']),
            last_update_date=date_from_geo_string(data['last_update_date']),
            submission_date=date_from_geo_string(data['submission_date']),
        )
        cls.add_platform(platform)
        return platform


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


class CharacteristicParser(BaseParser):
    def parse_tag(self):
        return self.element.get('tag')

    def parse_value(self):
        return self.element.text.strip()

    def parse(self):
        tag = self.parse_tag()
        value = self.parse_value()
        return Characteristic(
            tag=tag,
            value=value
        )

    @classmethod
    def parse_dict(cls, data):
        return Characteristic(
            tag=data['tag'],
            value=data['value']
        )


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


class ChannelParser(BaseParser):
    def parse_position(self):
        return int(self.element.get('position'))

    def parse_source(self):
        return self.element.xpath('./Source/text()')[0]

    def parse_organisms(self):
        organisms = []
        for element in self.element.xpath('./Organism'):
            parser = OrganismParser(element)
            organisms.append(parser.parse())
        return organisms

    def parse_characteristics(self):
        characteristics = []
        for element in self.element.xpath('./Characteristics'):
            parser = CharacteristicParser(element)
            characteristics.append(
                parser.parse()
            )
        return characteristics

    def parse_treatment_protocol(self):
        treatment_protocol = self.element.xpath('./Treatment-Protocol/text()')
        if treatment_protocol:
            return treatment_protocol[0].strip()
        return None

    def parse_growth_protocol(self):
        growth_protocol = self.element.xpath('./Growth-Protocol/text()')
        if growth_protocol:
            return growth_protocol[0].strip()
        return None

    def parse_molecule(self):
        molecule = self.element.xpath('./Molecule/text()')
        if molecule:
            return molecule[0]
        return None

    def parse_extract_protocol(self):
        extract_protocol = self.element.xpath('./Extract-Protocol/text()')
        if extract_protocol:
            return extract_protocol[0].strip()
        return None

    def parse_label(self):
        label = self.element.xpath('./Label/text()')
        if label:
            return label[0]
        return None

    def parse_label_protocol(self):
        label_protocol = self.element.xpath('./Label-Protocol/text()')
        if label_protocol:
            return label_protocol[0].strip()
        return None

    def parse(self):
        position = self.parse_position()
        source = self.parse_source()
        organisms = self.parse_organisms()
        characteristics = self.parse_characteristics()
        treatment_protocol = self.parse_treatment_protocol()
        growth_protocol = self.parse_growth_protocol()
        molecule = self.parse_molecule()
        extract_protocol = self.parse_extract_protocol()
        label = self.parse_label()
        label_protocol = self.parse_label_protocol()
        return Channel(
            position=position,
            source=source,
            organisms=organisms,
            characteristics=characteristics,
            treatment_protocol=treatment_protocol,
            growth_protocol=growth_protocol,
            molecule=molecule,
            extract_protocol=extract_protocol,
            label=label,
            label_protocol=label_protocol
        )

    @classmethod
    def parse_dict(cls, data):
        organisms = [
            OrganismParser.parse_dict(
                organism_data
            ) for organism_data in data['organisms']
        ]
        characteristics = [
            CharacteristicParser.parse_dict(
                characteristic_data
            ) for characteristic_data in data['characteristics']
        ]
        return Channel(
            position=data['position'],
            source=data['source'],
            organisms=organisms,
            characteristics=characteristics,
            treatment_protocol=data['treatment_protocol'],
            growth_protocol=data['growth_protocol'],
            molecule=data['molecule'],
            extract_protocol=data['extract_protocol'],
            label=data['label'],
            label_protocol=data['label_protocol'],
        )


class Sample(object):

    def __init__(
        self, title, accession, type,
        channel_count, channels,
        hybridization_protocol, scan_protocol,
        description, data_processing, supplementary_data,
        columns, internal_data, release_date,
        last_update_date, submission_date, platform
    ):
        self.title = title
        self.accession = accession
        self.type = type
        self.channel_count = channel_count
        self.channels = channels
        self.hybridization_protocol = hybridization_protocol
        self.scan_protocol = scan_protocol
        self.description = description
        self.data_processing = data_processing
        self.supplementary_data = supplementary_data
        self.columns = columns
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
        return (self.title == other.title) and (self.accession == other.accession) and (
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
            'release_date': self.release_date.strftime('%Y-%m-%d'),
            'last_update_date': self.last_update_date.strftime('%Y-%m-%d'),
            'submission_date': self.submission_date.strftime('%Y-%m-%d'),
            'platform': self.platform.to_dict()
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


class SampleParser(BaseParser):
    _samples = {}

    @classmethod
    def from_accession(cls, accession):
        url = geo_router.sample_detail(
            accession=accession,
            targ='self',
            form='xml',
            view='quick'
        )
        logger.info(f'accessing {url}.')
        req = urlopen(url)
        miniml = req.read()
        return cls.from_miniml(miniml)

    def parse_title(self):
        return self.element.xpath('/MINiML/Sample/Title/text()')[0]

    def parse_accession(self):
        return self.element.xpath('/MINiML/Sample/Accession/text()')[0]

    def parse_type(self):
        return self.element.xpath('/MINiML/Sample/Type/text()')[0]

    def parse_channel_count(self):
        return int(self.element.xpath('/MINiML/Sample/Channel-Count/text()')[0])

    def parse_channels(self):
        channels = []
        for element in self.element.xpath('/MINiML/Sample/Channel'):
            parser = ChannelParser(element)
            channels.append(parser.parse())
        return channels

    def parse_hybridization_protocol(self):
        hp = self.element.xpath('/MINiML/Sample/Hybridization-Protocol/text()')
        if hp:
            return hp[0].strip()
        return None

    def parse_scan_protocol(self):
        sp = self.element.xpath('/MINiML/Sample/Scan-Protocol/text()')
        if sp:
            return sp[0].strip()
        return None

    def parse_description(self):
        desc = self.element.xpath('/MINiML/Sample/Description/text()')
        if desc:
            return desc[0].strip()
        return None

    def parse_data_processing(self):
        dp = self.element.xpath('/MINiML/Sample/Data-Processing/text()')
        if dp:
            return dp[0].strip()
        return None

    def parse_supplementary_data(self):
        supplementary_data = []
        for element in self.element.xpath('/MINiML/Sample/Supplementary-Data'):
            parser = SupplementaryDataItemParser(element)
            supplementary_data.append(parser.parse())
        return supplementary_data

    def parse_columns(self):
        columns = []
        for element in self.element.xpath('/MINiML/Sample/Data-Table/Column'):
            parser = ColumnParser(element)
            columns.append(parser.parse())
        return columns

    def parse_internal_data(self):
        internal_data_text = self.element.xpath(
            '/MINiML/Sample/Data-Table/Internal-Data/text()'
        )
        if internal_data_text:
            internal_data_text = internal_data_text[0].strip()
            internal_data = []
            for line in internal_data_text.split('\n'):
                if not line:
                    continue
                internal_data.append(line.split('\t'))
            return internal_data
        return None

    def parse_release_date(self):
        return date_from_geo_string(
            self.element.xpath('/MINiML/Sample/Status/Release-Date/text()')[0]
        )

    def parse_last_update_date(self):
        return date_from_geo_string(
            self.element.xpath('/MINiML/Sample/Status/Last-Update-Date/text()')[0]
        )

    def parse_submission_date(self):
        return date_from_geo_string(
            self.element.xpath('/MINiML/Sample/Status/Submission-Date/text()')[0]
        )

    def parse_platform(self):
        accession = self.element.xpath('/MINiML/Platform/Accession/text()')[0]
        platform = PlatformParser.get_platform(accession)
        if not platform:
            parser = PlatformParser.from_accession(accession)
            platform = parser.parse()
        return platform

    @classmethod
    def add_sample(cls, sample):
        cls._samples[sample.accession] = sample

    @classmethod
    def get_sample(cls, accession):
        return cls._samples.get(accession, None)

    def parse(self):
        title = self.parse_title()
        accession = self.parse_accession()
        type = self.parse_type()
        channel_count = self.parse_channel_count()
        channels = self.parse_channels()
        hybridization_protocol = self.parse_hybridization_protocol()
        scan_protocol = self.parse_scan_protocol()
        description = self.parse_description()
        data_processing = self.parse_data_processing()
        supplementary_data = self.parse_supplementary_data()
        columns = self.parse_columns()
        internal_data = self.parse_internal_data()
        release_date = self.parse_release_date()
        last_update_date = self.parse_last_update_date()
        submission_date = self.parse_submission_date()
        platform = self.parse_platform()
        sample = Sample(
            title=title,
            accession=accession,
            type=type,
            channel_count=channel_count,
            channels=channels,
            hybridization_protocol=hybridization_protocol,
            scan_protocol=scan_protocol,
            description=description,
            data_processing=data_processing,
            supplementary_data=supplementary_data,
            columns=columns,
            internal_data=internal_data,
            release_date=release_date,
            last_update_date=last_update_date,
            submission_date=submission_date,
            platform=platform
        )
        self.add_sample(sample)
        return sample

    @classmethod
    def parse_dict(cls, data):
        channels = [
            ChannelParser.parse_dict(
                channel_data
            ) for channel_data in data['channels']
        ]
        supplementary_data = [
            SupplementaryDataItemParser.parse_dict(
                supplementary_data_item_data
            ) for supplementary_data_item_data in data['supplementary_data']
        ]
        columns = [
            ColumnParser.parse_dict(
                column_data
            ) for column_data in data['columns']
        ]
        platform = PlatformParser.parse_dict(data['platform'])
        sample = Sample(
            title=data['title'],
            accession=data['accession'],
            type=data['type'],
            channel_count=data['channel_count'],
            channels=channels,
            hybridization_protocol=data['hybridization_protocol'],
            scan_protocol=data['scan_protocol'],
            description=data['description'],
            data_processing=data['data_processing'],
            supplementary_data=supplementary_data,
            columns=columns,
            internal_data=data['internal_data'],
            release_date=date_from_geo_string(data['release_date']),
            last_update_date=date_from_geo_string(data['last_update_date']),
            submission_date=date_from_geo_string(data['submission_date']),
            platform=platform
        )
        cls.add_sample(sample)
        return sample


class Series(object):
    def __init__(
        self, title, accession, pmids, summary,
        overall_design, experiment_types, supplementary_data,
        release_date, last_update_date, submission_date, samples
    ):
        self.title = title
        self.accession = accession
        self.pmids = pmids
        self.summary = summary
        self.overall_design = overall_design
        self.experiment_types = experiment_types
        self.supplementary_data = supplementary_data
        self.release_date = release_date
        self.last_update_date = last_update_date
        self.submission_date = submission_date
        self.samples = samples

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
            'title': self.title,
            'accession': self.accession,
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
            'release_date': self.release_date.strftime('%Y-%m-%d'),
            'last_update_date': self.last_update_date.strftime('%Y-%m-%d'),
            'submission_date': self.submission_date.strftime('%Y-%m-%d'),
            'samples': [sample.to_dict() for sample in self.samples],
        }

    def set_samples(self, samples):
        self.samples = samples

    def add_sample(self, sample):
        self.samples.append(sample)

    @property
    def sample_count(self):
        return len(self.samples)

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


class SeriesParser(BaseParser):
    _series = {}

    @classmethod
    def from_accession(cls, accession):
        url = geo_router.series_detail(
            accession=accession,
            targ='self',
            form='xml',
            view='quick'
        )
        logger.info(f'accessing {url}.')
        req = urlopen(url)
        miniml = req.read()
        return cls.from_miniml(miniml)

    def parse_title(self):
        return self.element.xpath('/MINiML/Series/Title/text()')[0]

    def parse_accession(self):
        return self.element.xpath('/MINiML/Series/Accession/text()')[0]

    def parse_pmids(self):
        return self.element.xpath('/MINiML/Series/Pubmed-ID/text()')

    def parse_summary(self):
        return self.element.xpath('/MINiML/Series/Summary/text()')[0].strip()

    def parse_overall_design(self):
        return self.element.xpath('/MINiML/Series/Overall-Design/text()')[0].strip()

    def parse_experiment_types(self):
        experiment_types = []
        for element in self.element.xpath('/MINiML/Series/Type'):
            parser = ExperimentTypeParser(element)
            experiment_types.append(parser.parse())
        return experiment_types

    def parse_supplementary_data(self):
        supplementary_data = []
        for element in self.element.xpath('/MINiML/Series/Supplementary-Data'):
            supplementary_data.append(SupplementaryDataItem(
                type=element.get('type'),
                url=element.text.strip()
            ))
        return supplementary_data

    def parse_release_date(self):
        return date_from_geo_string(
            self.element.xpath('/MINiML/Series/Status/Release-Date/text()')[0]
        )

    def parse_last_update_date(self):
        return date_from_geo_string(
            self.element.xpath('/MINiML/Series/Status/Last-Update-Date/text()')[0]
        )

    def parse_submission_date(self):
        return date_from_geo_string(
            self.element.xpath('/MINiML/Series/Status/Submission-Date/text()')[0]
        )

    def parse_sample_accessions(self):
        return self.element.xpath('/MINiML/Sample/Accession/text()')

    def parse_samples(self):
        samples = []
        accessions = self.parse_sample_accessions()
        for accession in accessions:
            sample = SampleParser.get_sample(accession)
            if not sample:
                parser = SampleParser.from_accession(accession)
                sample = parser.parse()
            samples.append(sample)
        return samples

    @classmethod
    def add_series(cls, series):
        cls._series[series.accession] = series

    @classmethod
    def get_series(cls, accession):
        return cls._series.get(accession, None)

    def parse(self, parse_samples=True):
        """
        parse series
        Args:
            parse_samples: if parse samples, default yes
        Returns:
            Series object
        """
        title = self.parse_title()
        accession = self.parse_accession()
        pmids = self.parse_pmids()
        summary = self.parse_summary()
        overall_design = self.parse_overall_design()
        experiment_types = self.parse_experiment_types()
        supplementary_data = self.parse_supplementary_data()
        release_date = self.parse_release_date()
        last_update_date = self.parse_last_update_date()
        submission_date = self.parse_submission_date()
        if parse_samples:
            samples = self.parse_samples()
        else:
            samples = []
        series = Series(
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
            samples=samples
        )
        self.add_series(series)
        return series

    @classmethod
    def parse_dict(cls, data):
        experiment_types = [
            ExperimentTypeParser.parse_dict(
                experiment_type_data
            ) for experiment_type_data in data['experiment_types']
        ]
        supplementary_data = [
            SupplementaryDataItemParser.parse_dict(
                supplementary_data_item_data
            ) for supplementary_data_item_data in data['supplementary_data']
        ]
        samples = [
            SampleParser.parse_dict(
                sample_data
            ) for sample_data in data['samples']
        ]
        series = Series(
            title=data['title'],
            accession=data['accession'],
            pmids=data['pmids'],
            summary=data['summary'],
            overall_design=data['overall_design'],
            experiment_types=experiment_types,
            supplementary_data=supplementary_data,
            release_date=date_from_geo_string(data['release_date']),
            last_update_date=date_from_geo_string(data['last_update_date']),
            submission_date=date_from_geo_string(data['submission_date']),
            samples=samples
        )
        cls.add_series(series)
        return series


@click.group()
def geo_alchemy():
    pass


@geo_alchemy.command(name='series')
@click.option(
    '-a', '--accession',
    callback=validate_series_accession,
    help='GEO series accession'
)
def parse_series(accession):
    pass


if __name__ == '__main__':
    geo_alchemy()
