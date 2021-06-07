# -*- coding: utf-8 -*-
import geo_alchemy


class TestExperimentTypeParser(object):
    def parse_title(self, experiment_type_parser, experiment_type):
        assert experiment_type_parser == experiment_type


class TestSupplementaryDataItemParser(object):
    def test_parse_type(self, supplementary_data_item_parser):
        assert supplementary_data_item_parser.parse_type() == 'CEL'

    def test_parse_url(self, supplementary_data_item_parser):
        assert supplementary_data_item_parser.parse_url() == (
            'ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM1885nnn'
            '/GSM1885279/suppl/GSM1885279_LGSOC-Patient01_primary_tumor_cells.CEL.gz'
        )

    def test_parse(self, supplementary_data_item_parser):
        supplementary_data_item = geo_alchemy.SupplementaryDataItem(
            type='CEL',
            url=(
                'ftp://ftp.ncbi.nlm.nih.gov/geo/samples/GSM1885nnn/'
                'GSM1885279/suppl/GSM1885279_LGSOC-Patient01_primary_tumor_cells.CEL.gz'
            )
        )
        assert supplementary_data_item == supplementary_data_item_parser.parse()


class TestOrganismParser(object):
    def test_parse_taxid(self, organism_parser):
        assert organism_parser.parse_taxid() == '9606'

    def test_parse_sciname(self, organism_parser):
        assert organism_parser.parse_sciname() == 'Homo sapiens'

    def test_parse(self, organism_parser):
        organism = geo_alchemy.Organism(
            taxid='9606',
            sciname='Homo sapiens'
        )
        assert organism == organism_parser.parse()


class TestCharacteristicParser(object):
    def test_parse_tag(self, characteristic_parser):
        assert characteristic_parser.parse_tag() == 'tumor type'

    def test_parse_value(self, characteristic_parser):
        assert characteristic_parser.parse_value() == 'primary'

    def test_parse(self, characteristic_parser):
        characteristic = geo_alchemy.Characteristic(
            tag='tumor type',
            value='primary'
        )
        assert characteristic == characteristic_parser.parse()


class TestChannelParser(object):
    def test_parse_position(self, channel_parser):
        assert channel_parser.parse_position() == 1

    def test_parse_source(self, channel_parser):
        assert channel_parser.parse_source() == 'LGSOC patient primary tumor'

    def test_parse_organisms(self, channel_parser):
        organisms = [
            geo_alchemy.Organism(taxid='9606', sciname='Homo sapiens')
        ]
        assert organisms == channel_parser.parse_organisms()

    def test_parse_characteristics(self, channel_parser):
        characteristics = [
            geo_alchemy.Characteristic(
                tag='tumor type',
                value='primary'
            )
        ]
        assert channel_parser.parse_characteristics() == characteristics

    def test_parse_treatment_protocol(self, channel_parser):
        assert channel_parser.parse_treatment_protocol() is None

    def test_parse_growth_protocol(self, channel_parser):
        assert channel_parser.parse_growth_protocol() is None

    def test_parse_molecule(self, channel_parser):
        assert channel_parser.parse_molecule() == 'total RNA'

    def test_parse_extract_protocol(self, channel_parser):
        assert channel_parser.parse_extract_protocol() == (
            "Isolation of RNA was performed using the Trizol "
            "method (Invitrogen) and was purified using RNeasy "
            "spin columns (Qiagen) according to the manufacturers' protocols."
        )

    def test_parse_label(self, channel_parser):
        assert channel_parser.parse_label() == 'biotin'

    def test_parse_label_protocol(self, channel_parser):
        assert channel_parser.parse_label_protocol() == (
            'Label protocol was carried out according to the '
            'Eukaryotic Target Preparation protocol in the '
            'Affymetrix technical manual (701021 Rev. 5) '
            'for Genechip Expression analysis (Affymetrix).'
        )

    def test_parse(self, channel_parser):
        extract_protocol = (
            "Isolation of RNA was performed using the Trizol "
            "method (Invitrogen) and was purified using RNeasy "
            "spin columns (Qiagen) according to the manufacturers' protocols."
        )
        label_protocol = (
            'Label protocol was carried out according to the '
            'Eukaryotic Target Preparation protocol in the '
            'Affymetrix technical manual (701021 Rev. 5) '
            'for Genechip Expression analysis (Affymetrix).'
        )
        channel = geo_alchemy.Channel(
            position=1,
            source='LGSOC patient primary tumor',
            organisms=[geo_alchemy.Organism(
                taxid='9606',
                sciname='Homo sapiens'
            )],
            characteristics=[geo_alchemy.Characteristic(
                tag='tumor type',
                value='primary'
            )],
            treatment_protocol=None,
            growth_protocol=None,
            molecule='total RNA',
            extract_protocol=extract_protocol,
            label='biotin',
            label_protocol=label_protocol
        )
        assert channel == channel_parser.parse()


class TestColumnParser(object):
    def test_parse_position(self, column_parser):
        assert column_parser.parse_position() == 2

    def test_parse_name(self, column_parser):
        assert column_parser.parse_name() == 'VALUE'

    def test_parse_description(self, column_parser):
        assert column_parser.parse_description() == (
            'MAS5.0 signal intensity'
        )

    def test_parse_parse(self, column_parser):
        column = geo_alchemy.Column(
            position=2,
            name='VALUE',
            description='MAS5.0 signal intensity'
        )
        assert column_parser.parse() == column


class TestPlatformParser(object):

    def test_parse_title(self, platform_parser, platform):
        assert platform_parser.parse_title() == platform.title

    def test_parse_accession(self, platform_parser, platform):
        assert platform_parser.parse_accession() == platform.accession

    def test_parse_technology(self, platform_parser, platform):
        assert platform_parser.parse_technology() == platform.technology

    def test_parse_distribution(self, platform_parser, platform):
        assert platform_parser.parse_distribution() == platform.distribution

    def test_parse_organisms(self, platform_parser, platform):
        assert platform_parser.parse_organisms() == platform.organisms

    def test_parse_manufacturer(self, platform_parser, platform):
        assert platform_parser.parse_manufacturer() == platform.manufacturer

    def test_parse_manufacturer_protocol(self, platform_parser, platform):
        assert platform_parser.parse_manufacturer_protocol() == platform.manufacturer_protocol

    def test_parse_description(self, platform_parser, platform):
        assert platform_parser.parse_description() == platform.description

    def test_parse_columns(self, platform_parser, platform):
        assert platform_parser.parse_columns() == platform.columns

    def test_parse_internal_data(self, platform_parser, platform):
        assert platform_parser.parse_internal_data() == platform.internal_data

    def test_parse_release_date(self, platform_parser, platform):
        assert platform_parser.parse_release_date() == platform.release_date

    def test_parse_last_update_date(self, platform_parser, platform):
        assert platform_parser.parse_last_update_date() == platform.last_update_date

    def test_parse_submission_date(self, platform_parser, platform):
        assert platform_parser.parse_submission_date() == platform.submission_date

    def test_parse(self, platform_parser, platform):
        assert len(platform_parser.platforms) == 0
        assert platform_parser.parse() == platform
        assert len(platform_parser.platforms) == 1
        platform_parser.parse()
        assert len(platform_parser.platforms) == 1

    def test_parse_dict(self, platform):
        assert geo_alchemy.PlatformParser.parse_dict(platform.to_dict()) == platform


class TestSampleParser(object):

    def test_parse_title(self, sample_parser, sample):
        assert sample_parser.parse_title() == sample.title

    def test_parse_accession(self, sample_parser, sample):
        assert sample_parser.parse_accession() == sample.accession

    def test_parse_type(self, sample_parser, sample):
        assert sample_parser.parse_type() == sample.type

    def test_parse_channel_count(self, sample_parser, sample):
        assert sample_parser.parse_channel_count() == sample.channel_count

    def test_parse_channels(self, sample_parser, sample):
        assert sample_parser.parse_channels() == sample.channels

    def test_parse_hybridization_protocol(self, sample_parser, sample):
        assert sample_parser.parse_hybridization_protocol() == sample.hybridization_protocol

    def test_parse_scan_protocol(self, sample_parser, sample):
        assert sample_parser.parse_scan_protocol() == sample.scan_protocol

    def test_parse_description(self, sample_parser, sample):
        assert sample_parser.parse_description() == sample.description

    def test_parse_data_processing(self, sample_parser, sample):
        assert sample_parser.parse_data_processing() == sample.data_processing

    def test_parse_supplementary_data(self, sample_parser, sample):
        assert sample_parser.parse_supplementary_data() == sample.supplementary_data

    def test_parse_columns(self, sample_parser, sample):
        assert sample_parser.parse_columns() == sample.columns

    def test_parse_internal_data(self, sample_parser, sample):
        assert sample_parser.parse_internal_data() == sample.internal_data

    def test_parse_release_date(self, sample_parser, sample):
        assert sample_parser.parse_release_date() == sample.release_date

    def test_parse_last_update_date(self, sample_parser, sample):
        assert sample_parser.parse_last_update_date() == sample.last_update_date

    def test_parse_submission_date(self, sample_parser, sample):
        assert sample_parser.parse_submission_date() == sample.submission_date

    def test_parse_platform(self, sample_parser, sample):
        platform = sample_parser.parse_platform()
        assert platform == sample.platform

    def test_parse(self, sample_parser, sample):
        assert sample_parser.parse() == sample

    def test_parse_dict(self, sample):
        assert geo_alchemy.SampleParser.parse_dict(sample.to_dict()) == sample

    def test_organisms(self, sample, organism):
        assert sample.organisms == [organism]


class TestSeriesParser(object):
    def test_parse_title(self, series_parser, series):
        assert series_parser.parse_title() == series.title

    def test_parse_accession(self, series_parser, series):
        assert series_parser.parse_accession() == series.accession

    def test_parse_pmids(self, series_parser, series):
        assert series_parser.parse_pmids() == series.pmids

    def test_parse_summary(self, series_parser, series):
        assert series_parser.parse_summary() == series.summary

    def test_parse_overall_design(self, series_parser, series):
        assert series_parser.parse_overall_design() == series.overall_design

    def test_parse_experiment_types(self, series_parser, series):
        assert series_parser.parse_experiment_types() == series.experiment_types

    def test_parse_supplementary_data(self, series_parser, series):
        assert series_parser.parse_supplementary_data() == series.supplementary_data

    def test_parse_release_date(self, series_parser, series):
        assert series_parser.parse_release_date() == series.release_date

    def test_parse_last_update_date(self, series_parser, series):
        assert series_parser.parse_last_update_date() == series.last_update_date

    def test_parse_submission_date(self, series_parser, series):
        assert series_parser.parse_submission_date() == series.submission_date

    def test_parse_dict(self, series):
        assert geo_alchemy.SeriesParser.parse_dict(series.to_dict()) == series

    def test_sample_count(self, series_parser, series):
        temp = series_parser.parse()
        assert temp.sample_count == 9
        assert temp.samples[0] == series.samples[0]

    def test_platforms(self, series_parser, series):
        assert series_parser.parse().platforms == series.platforms

    def test_organisms(self, series_parser, series):
        assert series_parser.parse().organisms == series.organisms
