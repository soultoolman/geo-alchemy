# geo-alchemy
a Python library and command line tool to make GEO data into gold.

1. [why geo-alchemy](#why-geo-alchemy)
2. [installation](#installation)
3. [use as Python library](#use-as-python-library)
    - [parse metadata from GEO](#parse-metadata-from-geo)
        - [parse platform](#parse-platform)
        - [parse sample](#parse-sample)
        - [parse series](#parse-series)
    - [serialization and deserialization](#serialization-and-deserialization)
4. [use as command line software](#use-as-command-line-software)
   - [preprocessing](#preprocessingmicroarray-series-only)

## why geo-alchemy

GEO is like a gold mine that contains a huge many gold ore.
But processing these gold ore(GEO series) into gold(expression matrix, clinical data) is not very easy:

1. how to map microarray probe to gene?
2. how about multiple probes map to same gene?
3. hot to get clinical data?
4. ...

geo-alchemy was born to deal with it.

## installation

If you only want use as Python library:

```
pip install geo-alchemy
```

If you also want use as command line software:

```
pip install 'geo-alchemy[cmd]'
```

## use as Python library

### parse metadata from GEO

#### parse platform

```python
from geo_alchemy import PlatformParser


parser = PlatformParser.from_accession('GPL570')
platform1 = parser.parse()


# or
platform2 = PlatformParser.from_accession('GPL570').parse()


print(platform1 == platform2)

# get platform annotation data
platform = PlatformParser.from_accession('GPL570', view='full').parse()
print(platform.internal_data)
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

# or
series2 = SeriesParser.from_accession('GSE73091').parse()


print(series1 == series2)
print(series1.platforms)
print(series1.samples)
print(series1.organisms)
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

## use as command line software

### preprocessing(microarray series only)

```
geo-alchemy pp -s GSE174772 -p GPL570 -g 11
```

1. `-s GSE174772` means preprocessing for GSE174772
2. `-p GPL570` means preprocessing samples who use GPL570 of GSE174772
3. `-g 11` means NO.11 column of GPL570 annotation file is gene

this command generate 2 files under current directory:

1. clinical file `GSE174772_clinical.txt`
2. gene expression file `GSE174772_expression.txt`
