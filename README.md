# geo-alchemy
a Python library and command line tool to make GEO data into gold.

1. [why geo-alchemy](#why-geo-alchemy)
2. [installation](#installation)
3. [usage](#usage)
    - [parse metadata from GEO](#parse-metadata-from-geo)
        - [parse platform](#parse-platform)
        - [parse sample](#parse-sample)
        - [parse series](#parse-series)
    - [serialization and deserialization](#serialization-and-deserialization)

## why geo-alchemy

GEO is like a gold mine that contains a huge many gold ore.
But processing these gold ore(GEO series) into gold(expression matrix, clinical data) is not very easy:

1. how to map microarray probe to gene?
2. how about multiple probes map to same gene?
3. hot to get clinical data?
4. ...

geo-alchemy was born to deal with it.

## installation

```
pip install geo-alchemy
```

## usage

### parse metadata from GEO

#### parse platform

```python
from geo_alchemy import PlatformParser


parser = PlatformParser.from_accession('GPL570')
platform1 = parser.parse()


# or
platform2 = PlatformParser.from_accession('GPL570').parse()


print(platform1 == platform2)
```

#### parse sample

```python
from geo_alchemy import SampleParser


parser = SampleParser.from_accession('GSM1885279')
sample1 = parser.parse()

# or
sample2 = SampleParser.from_accession('GSM1885279').parse()

print(sample1 == sample2)
```

#### parse series

```python
from geo_alchemy import SeriesParser


parser = SeriesParser.from_accession('GSE73091')
series1 = parser.parse()


# don't parse samples, samples attribute will be a blank list
series2 = parser.parse(parse_samples=False)
print(series2.samples == [])


# or
series3 = SeriesParser.from_accession('GSE73091').parse()


print(series1 == series3)
```

additional computed attributes can be access by:

```python
print(series.sample_count)  # how many samples
print(series.platforms)  # duplication removal platforms
print(series.organisms)  # duplication removal organisms
```

### serialization and deserialization

For the convenience of saving, all objects in geo-alchemy can be converted to dict, 
and this dict can be directly saved to a file in json form.

Moreover, geo-alchemy also provides methods to convert these dicts into objects.


```python
from geo_alchemy import SeriesParser


series1 = SeriesParser.from_accession('GSE73091').parse()
data = series1.to_dict()
series2 = SeriesParser.parse_dict(data)


print(series1 == series2)
```
