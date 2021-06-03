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
    - [crawl all GEO metadata](#crawl-all-geo-metadata)
      - [crawl platform metadata](#crawl-platform-metadata)
      - [crawl sample metadata](#crawl-sample-metadata)
      - [crawl series metadata](#crawl-sample-metadata)
      - [multiple processes](#multiple-processes)
      - [what is jsonlines](#whats-jsonlines)

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

### crawl all GEO metadata

geo-alchemy also support whole site crawling, support features:

1. crawling all platform metadata.
2. crawling all sample metadata.
3. crawling all series metadata.
4. incremental crawling.
5. crawling sample metadata based on existing platform metadata.
6. crawling series metadata based on existing platform metadata and series metadata.
7. multiple processes support.

#### crawl platform metadata

##### denovo crawling

```
geo-alchemy crawl platforms -o platforms.jl
```

##### incremental crawling

```
geo-alchemy crawl platforms -cf platforms.jl -o new-platforms.jl
```

#### crawl sample metadata

##### denovo crawling

```
geo-alchemy crawl samples -o samples.jl
```

##### incremental crawling

```
geo-alchemy crawl samples -cf samples.jl -o new-samples.jl
```

##### based on existing platform metadata jsonlines file

When parse sample metadata, the specified platform metadata will also
be crawled. If you want to omit these network accessing, you can
specify the platform metadata jsonlines file crawled.

```
geo-alchemy crawl samples -cpf platforms.jl -cf samples.jl -o new-samples.jl
```

#### crawl series metadata

##### denovo crawling

```
geo-alchemy crawl series -o series.jl
```

##### incremental crawling

```
geo-alchemy crawl series -cf series.jl -o new-series.jl
```

##### based on existing platform and sample metadata jsonlines file

like sample, you can:

```
geo-alchemy crawl series -cpf platforms.jl -csf samples.jl -cf series.jl -o new-series.jl
```

#### multiple processes

To accelerate crawling, geo-alchemy support multiple processes.

eg, use 10 processes:

```
geo-alchemy crawl platform -p 10 -o platforms.jl
```

#### what's jsonlines

Refer to [this site](https://jsonlines.org/) for details.
