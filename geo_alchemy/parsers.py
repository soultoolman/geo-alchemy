# -*- coding: utf-8 -*-
from lxml import etree

from .utils import (
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
    def __init__(self, element, rm_ns=True):
        if rm_ns:
            element = remove_namespace(element)
        self.element = element

    @classmethod
    def from_miniml(cls, miniml):
        element = etree.fromstring(
            miniml, parser=etree.XMLParser(huge_tree=True)
        )
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
    def from_accession(cls, accession, targ='self', form='xml', view='quick'):
        url = geo_router.platform_detail(
            accession=accession,
            targ=targ,
            form=form,
            view=view
        )
        downloader = HttpDownloader(DEFAULT_RETRIES)
        req = downloader.dl(url)
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
        cls.platforms[platform.accession] = platform

    @classmethod
    def get_platform(cls, accession):
        return cls.platforms.get(accession, None)

    @classmethod
    def clear_all_platforms(cls):
        cls.platforms.clear()

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
        self.platforms[accession] = platform
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

    @classmethod
    def crawl_accessions(cls, zsort='date', display=20, page=1):
        url = geo_router.platform_list(zsort, display, page)
        downloader = HttpDownloader(DEFAULT_RETRIES)
        req = downloader.dl(url)
        element = remove_namespace(
            etree.fromstring(req.read(), parser=etree.XMLParser(huge_tree=True))
        )
        accessions = element.xpath('//table[@id="geo_data"]/tbody/tr/td[1]/a/text()')
        has_next = bool(element.xpath('//div[@class="pager"]/span[@class="next"]'))
        return accessions, has_next


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
    def from_accession(cls, accession, targ='self', form='xml', view='quick'):
        url = geo_router.sample_detail(
            accession=accession,
            targ=targ,
            form=form,
            view=view
        )
        downloader = HttpDownloader(DEFAULT_RETRIES)
        req = downloader.dl(url)
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
        cls.samples[sample.accession] = sample

    @classmethod
    def get_sample(cls, accession):
        return cls.samples.get(accession, None)

    @classmethod
    def clear_all_samples(cls):
        return cls.samples.clear()

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

    @classmethod
    def crawl_accessions(cls, zsort='date', display=20, page=1):
        url = geo_router.sample_list(zsort, display, page)
        downloader = HttpDownloader(DEFAULT_RETRIES)
        req = downloader.dl(url)
        element = remove_namespace(
            etree.fromstring(req.read(), parser=etree.XMLParser(huge_tree=True))
        )
        accessions = element.xpath('//table[@id="geo_data"]/tbody/tr/td[1]/a/text()')
        has_next = bool(element.xpath('//div[@class="pager"]/span[@class="next"]'))
        return accessions, has_next


class SeriesParser(BaseParser):
    series = {}

    @classmethod
    def from_accession(cls, accession, targ='self', form='xml', view='quick'):
        url = geo_router.series_detail(
            accession=accession,
            targ=targ,
            form=form,
            view=view
        )
        downloader = HttpDownloader(DEFAULT_RETRIES)
        req = downloader.dl(url)
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
        cls.series[series.accession] = series

    @classmethod
    def get_series(cls, accession):
        return cls.series.get(accession, None)

    @classmethod
    def clear_all_series(cls):
        cls.series.clear()

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

    @classmethod
    def crawl_accessions(cls, zsort='date', display=20, page=1):
        url = geo_router.series_list(zsort, display, page)
        downloader = HttpDownloader(DEFAULT_RETRIES)
        req = downloader.dl(url)
        element = remove_namespace(
            etree.fromstring(req.read(), parser=etree.XMLParser(huge_tree=True))
        )
        accessions = element.xpath('//table[@id="geo_data"]/tbody/tr/td[1]/a/text()')
        has_next = bool(element.xpath('//div[@class="pager"]/span[@class="next"]'))
        return accessions, has_next
