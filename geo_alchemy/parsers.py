# -*- coding: utf-8 -*-
from lxml import etree

from .utils import (
    get_first,
    remove_namespace,
    date_from_geo_string,
    HttpDownloader,
    DEFAULT_RETRIES,
)
from .geo import (
    geo_router,
    SupplementaryDataItem,
    Organism,
    ExperimentType,
    Column,
    Platform,
    Characteristic,
    Channel,
    Sample,
    Series
)


class BaseParser(object):
    xml_parser = etree.XMLParser(huge_tree=True)

    def __init__(self, element):
        self.element = element

    @classmethod
    def from_miniml(cls, miniml):
        raise NotImplemented

    @classmethod
    def from_miniml_file(cls, miniml_file):
        with open(miniml_file, 'rb') as fp:
            miniml = fp.read()
        return cls.from_miniml(miniml)

    @classmethod
    def from_accession(cls, accession):
        raise NotImplemented

    def parse_release_date(self):
        text = get_first(self.element.xpath('./Status/Release-Date/text()'))
        return date_from_geo_string(text) if text else None

    def parse_last_update_date(self):
        text = get_first(self.element.xpath('./Status/Last-Update-Date/text()'))
        return date_from_geo_string(text) if text else None

    def parse_submission_date(self):
        text = get_first(self.element.xpath('./Status/Submission-Date/text()'))
        return date_from_geo_string(text) if text else None

    def parse(self):
        raise NotImplemented


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


class PlatformParser(BaseParser):
    platforms = {}

    @classmethod
    def from_miniml(cls, miniml):
        element = remove_namespace(etree.fromstring(miniml, parser=cls.xml_parser))
        return cls(element.xpath('/MINiML/Platform')[0])

    @classmethod
    def from_accession(cls, accession, targ='self', form='xml', view='quick'):
        url = geo_router.platform_detail(
            accession=accession,
            targ=targ,
            form=form,
            view=view
        )
        downloader = HttpDownloader(DEFAULT_RETRIES)
        req = downloader.dl(url)
        return cls.from_miniml(req.read())

    @classmethod
    def from_series_miniml_element(cls, miniml_element):
        return [cls(element) for element in miniml_element.xpath('/MINiML/Platform')]

    @classmethod
    def get_or_parse(cls, accession):
        if accession in cls.platforms:
            return cls.platforms[accession]
        return cls.from_accession(accession).parse()

    def parse_accession(self):
        return self.element.xpath('./Accession/text()')[0]

    def parse_title(self):
        return get_first(self.element.xpath('./Title/text()'))

    def parse_technology(self):
        return get_first(self.element.xpath('./Technology/text()'))

    def parse_distribution(self):
        return get_first(self.element.xpath('./Distribution/text()'))

    def parse_organisms(self):
        organisms = []
        for element in self.element.xpath('./Organism'):
            parser = OrganismParser(element)
            organisms.append(parser.parse())
        return organisms

    def parse_manufacturer(self):
        return get_first(
            self.element.xpath('./Manufacturer/text()'),
            strip=True
        )

    def parse_manufacturer_protocol(self):
        return get_first(
            self.element.xpath('./Manufacture-Protocol/text()'),
            strip=True
        )

    def parse_description(self):
        return get_first(
            self.element.xpath('./Description/text()'),
            strip=True
        )

    def parse_columns(self):
        columns = []
        for element in self.element.xpath('./Data-Table/Column'):
            parser = ColumnParser(element)
            columns.append(parser.parse())
        return columns

    def parse_internal_data(self):
        internal_data_text = self.element.xpath(
            './Data-Table/Internal-Data/text()'
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

    @classmethod
    def add_platform(cls, platform):
        if not platform.is_malformed:
            cls.platforms[platform.accession] = platform

    @classmethod
    def get_platform(cls, accession):
        return cls.platforms.get(accession, None)

    @classmethod
    def clear_all_platforms(cls):
        cls.platforms.clear()

    def parse(self, lazy=True):
        accession = self.parse_accession()
        if lazy and (accession in self.platforms):
            return self.platforms[accession]
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
        self.platforms[accession] = platform
        return platform

    @classmethod
    def parse_dict(cls, data):
        if data['accession'] in cls.platforms:
            return cls.platforms[data['accession']]
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
            accession=data['accession'],
            title=data['title'],
            technology=data['technology'],
            distribution=data['distribution'],
            organisms=organisms,
            manufacturer=data['manufacturer'],
            manufacturer_protocol=data['manufacturer_protocol'],
            description=data['description'],
            columns=columns,
            internal_data=data['internal_data'],
            release_date=date_from_geo_string(
                data['release_date']
            ) if data['release_date'] else None,
            last_update_date=date_from_geo_string(
                data['last_update_date']
            ) if data['last_update_date'] else None,
            submission_date=date_from_geo_string(
                data['submission_date']
            ) if data['submission_date'] else None,
        )
        cls.add_platform(platform)
        return platform


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


class SampleParser(BaseParser):
    samples = {}

    @classmethod
    def from_miniml(cls, miniml):
        element = remove_namespace(etree.fromstring(miniml, parser=cls.xml_parser))
        return cls(element.xpath('Sample')[0])

    @classmethod
    def from_accession(cls, accession, targ='self', form='xml', view='quick'):
        url = geo_router.sample_detail(
            accession=accession,
            targ=targ,
            form=form,
            view=view
        )
        downloader = HttpDownloader(DEFAULT_RETRIES)
        req = downloader.dl(url)
        return cls.from_miniml(req.read())

    @classmethod
    def from_series_miniml_element(cls, miniml_element):
        return [cls(element) for element in miniml_element.xpath('/MINiML/Sample')]

    @classmethod
    def get_or_parse(cls, accession):
        if accession in cls.samples:
            return cls.samples[accession]
        return cls.from_accession(accession).parse()

    def parse_accession(self):
        return self.element.xpath('./Accession/text()')[0]

    def parse_title(self):
        return get_first(self.element.xpath('./Title/text()'))

    def parse_type(self):
        return get_first(self.element.xpath('./Type/text()'))

    def parse_channel_count(self):
        channel_count = get_first(self.element.xpath('./Channel-Count/text()'))
        if channel_count is not None:
            channel_count = int(channel_count)
        return channel_count

    def parse_channels(self):
        channels = []
        for element in self.element.xpath('./Channel'):
            parser = ChannelParser(element)
            channels.append(parser.parse())
        return channels

    def parse_hybridization_protocol(self):
        return get_first(
            self.element.xpath('./Hybridization-Protocol/text()'),
            strip=True
        )

    def parse_scan_protocol(self):
        return get_first(
            self.element.xpath('./Scan-Protocol/text()'),
            strip=True
        )

    def parse_description(self):
        return get_first(
            self.element.xpath('./Description/text()'),
            strip=True
        )

    def parse_data_processing(self):
        return get_first(
            self.element.xpath('./Data-Processing/text()'),
            strip=True
        )

    def parse_supplementary_data(self):
        supplementary_data = []
        for element in self.element.xpath('./Supplementary-Data'):
            parser = SupplementaryDataItemParser(element)
            supplementary_data.append(parser.parse())
        return supplementary_data

    def parse_columns(self):
        columns = []
        for element in self.element.xpath('./Data-Table/Column'):
            parser = ColumnParser(element)
            columns.append(parser.parse())
        return columns

    def parse_internal_data(self):
        internal_data_text = get_first(
            self.element.xpath('./Data-Table/Internal-Data/text()'),
            strip=True
        )
        if not internal_data_text:
            return None
        internal_data = []
        for line in internal_data_text.split('\n'):
            if not line:
                continue
            internal_data.append(line.split('\t'))
        return internal_data

    def get_platform_accession(self):
        return get_first(self.element.xpath('./Platform-Ref/@ref'))

    def parse_platform(self):
        accession = self.get_platform_accession()
        if not accession:
            return None
        return PlatformParser.get_or_parse(accession)

    @classmethod
    def add_sample(cls, sample):
        if not sample.is_malformed:
            cls.samples[sample.accession] = sample

    @classmethod
    def get_sample(cls, accession):
        return cls.samples.get(accession, None)

    @classmethod
    def clear_all_samples(cls):
        return cls.samples.clear()

    def parse(self, lazy=True):
        accession = self.parse_accession()
        if lazy and (accession in self.samples):
            return self.samples[accession]
        title = self.parse_title()
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
            accession=accession,
            title=title,
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
        if data['accession'] in cls.samples:
            return cls.samples[data['accession']]
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
            accession=data['accession'],
            title=data['title'],
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


class SeriesParser(BaseParser):
    series = {}

    @classmethod
    def from_miniml(cls, miniml):
        element = remove_namespace(etree.fromstring(miniml, parser=cls.xml_parser))
        return cls(element.xpath('/MINiML/Series')[0])

    @classmethod
    def from_accession(cls, accession, targ='all', form='xml', view='quick'):
        url = geo_router.series_detail(
            accession=accession,
            targ=targ,
            form=form,
            view=view
        )
        downloader = HttpDownloader(DEFAULT_RETRIES)
        req = downloader.dl(url)
        return cls.from_miniml(req.read())

    @classmethod
    def get_or_parse(cls, accession):
        if accession in cls.series:
            return cls.series[accession]
        return cls.from_accession(accession).parse()

    def parse_accession(self):
        return self.element.xpath('./Accession/text()')[0]

    def parse_title(self):
        return get_first(self.element.xpath('./Title/text()'))

    def parse_pmids(self):
        return self.element.xpath('./Pubmed-ID/text()')

    def parse_summary(self):
        return get_first(
            self.element.xpath('./Summary/text()'),
            strip=True
        )

    def parse_overall_design(self):
        return get_first(
            self.element.xpath('./Overall-Design/text()'),
            strip=True
        )

    def parse_experiment_types(self):
        experiment_types = []
        for element in self.element.xpath('./Type'):
            parser = ExperimentTypeParser(element)
            experiment_types.append(parser.parse())
        return experiment_types

    def parse_supplementary_data(self):
        supplementary_data = []
        for element in self.element.xpath('./Supplementary-Data'):
            supplementary_data.append(SupplementaryDataItem(
                type=element.get('type'),
                url=element.text.strip()
            ))
        return supplementary_data

    def parse_sample_accessions(self):
        return self.element.xpath('./Sample-Ref/@ref')

    def parse_samples(self):
        accessions = self.parse_sample_accessions()
        return [SampleParser.get_or_parse(accession) for accession in accessions]

    @classmethod
    def add_series(cls, series):
        if not series.is_malformed:
            cls.series[series.accession] = series

    @classmethod
    def get_series(cls, accession):
        return cls.series.get(accession, None)

    @classmethod
    def clear_all_series(cls):
        cls.series.clear()

    def parse(self, lazy=True):
        accession = self.parse_accession()
        if lazy and (accession in self.series):
            return self.series[accession]
        element = self.element.getparent()
        for parser in PlatformParser.from_series_miniml_element(element):
            parser.parse()
        for parser in SampleParser.from_series_miniml_element(element):
            parser.parse()
        title = self.parse_title()
        pmids = self.parse_pmids()
        summary = self.parse_summary()
        overall_design = self.parse_overall_design()
        experiment_types = self.parse_experiment_types()
        supplementary_data = self.parse_supplementary_data()
        release_date = self.parse_release_date()
        last_update_date = self.parse_last_update_date()
        submission_date = self.parse_submission_date()
        samples = self.parse_samples()
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
        if data['accession'] in cls.series:
            return cls.series[data['accession']]
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
