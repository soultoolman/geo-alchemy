# -*- coding: utf-8 -*-
import pytest

import geo_alchemy


class TestGeoRouter(object):
    def test_list(self):
        url = geo_alchemy.geo_router._list('samples')
        assert url == 'https://www.ncbi.nlm.nih.gov/geo/browse?view=samples&zsort=date&display=20&page=1'

    def test_detail(self):
        url = geo_alchemy.geo_router._detail('GSM1885279')
        assert url == 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM1885279&targ=self&form=xml&view=quick'

    def test_series_list(self):
        url = geo_alchemy.geo_router.series_list()
        assert url == 'https://www.ncbi.nlm.nih.gov/geo/browse?view=series&zsort=date&display=20&page=1'

    def test_series_list_page2(self):
        url = geo_alchemy.geo_router.series_list(page=2)
        assert url == 'https://www.ncbi.nlm.nih.gov/geo/browse?view=series&zsort=date&display=20&page=2'

    def test_sample_list(self):
        url = geo_alchemy.geo_router.sample_list()
        assert url == 'https://www.ncbi.nlm.nih.gov/geo/browse?view=samples&zsort=date&display=20&page=1'

    def test_sample_list_page2(self):
        url = geo_alchemy.geo_router.sample_list(page=2)
        assert url == 'https://www.ncbi.nlm.nih.gov/geo/browse?view=samples&zsort=date&display=20&page=2'

    def test_platform_list(self):
        url = geo_alchemy.geo_router.platform_list()
        assert url == 'https://www.ncbi.nlm.nih.gov/geo/browse?view=platforms&zsort=date&display=20&page=1'

    def test_platform_list_page2(self):
        url = geo_alchemy.geo_router.platform_list(page=2)
        assert url == 'https://www.ncbi.nlm.nih.gov/geo/browse?view=platforms&zsort=date&display=20&page=2'

    def test_series_detail(self):
        with pytest.raises(geo_alchemy.GeoAlchemyError):
            geo_alchemy.geo_router.series_detail('GPL570')
        url = geo_alchemy.geo_router.series_detail('GSE73091')
        assert url == 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE73091&targ=all&form=xml&view=quick'

    def test_sample_detail(self):
        with pytest.raises(geo_alchemy.GeoAlchemyError):
            geo_alchemy.geo_router.sample_detail('GSE73091')
        url = geo_alchemy.geo_router.sample_detail('GSM1885279')
        assert url == 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM1885279&targ=self&form=xml&view=quick'

    def test_platform_detail(self):
        with pytest.raises(geo_alchemy.GeoAlchemyError):
            geo_alchemy.geo_router.platform_detail('GSE73091')
        url = geo_alchemy.geo_router.platform_detail('GPL570')
        assert url == 'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GPL570&targ=self&form=xml&view=quick'
