# Hourly Energy Production for Switzerland

> Prototyping to understand the data for the challenge owned by the Swiss Federal
Office of Energy (SFOE) in the Energy Data Hackdays 7-8 May in Lausanne.

<!-- vim-markdown-toc Marked -->

* [In short](#in-short)
    * [The challenge](#the-challenge)
    * [Importance](#importance)
    * [The problem](#the-problem)
    * [Task & Requirements](#task-&-requirements)
* [Data](#data)
    * [SFOE daily time series](#sfoe-daily-time-series)
        * [Understand the SFOE data](#understand-the-sfoe-data)
        * [Download](#download)
            * [CSV data](#csv-data)
            * [JSON data via the Web API](#json-data-via-the-web-api)
                * [Get JSON data](#get-json-data)
                * [Convert JSON to CSV](#convert-json-to-csv)
        * [Verify integrity ?](#verify-integrity-?)
        * [Work with a sample ?](#work-with-a-sample-?)
        * [Convert to wide table](#convert-to-wide-table)
    * [Swissgrid](#swissgrid)
        * [Understand the Swissgrid data](#understand-the-swissgrid-data)
            * [Sample statistics](#sample-statistics)
    * [ENTSO‑E hourly time series](#entso‑e-hourly-time-series)
        * [Understand the ENTSO-E data](#understand-the-entso-e-data)
        * [Manual download](#manual-download)
            * [Other sources ?](#other-sources-?)
        * [Extract data for Switzerland](#extract-data-for-switzerland)
        * [Convert MWh to GWh](#convert-mwh-to-gwh)
        * [Convert to wide table](#convert-to-wide-table)
            * [Diagnose the data structure](#diagnose-the-data-structure)
            * [Unsparsify the data](#unsparsify-the-data)
            * [Reshape to wide table](#reshape-to-wide-table)
    * [Compare time series](#compare-time-series)
        * [SFOE vs Swissgrid](#sfoe-vs-swissgrid)
        * [SFOE vs ENTSOE](#sfoe-vs-entsoe)
            * [Link SFOE and ENTSO-E data](#link-sfoe-and-entso-e-data)
            * [Electricity generation types](#electricity-generation-types)
            * [Mapping ENTSO-E to SFOE types](#mapping-entso-e-to-sfoe-types)
            * [Combining Speicherkraft types](#combining-speicherkraft-types)
                * ["Speicherkraft" production](#"speicherkraft"-production)
                * [Production without "Speicherkraft"](#production-without-"speicherkraft")
                * [Restore lost field `DailyProduction_GWh`](#restore-lost-field-`dailyproduction_gwh`)
            * [Combine in one data file](#combine-in-one-data-file)
            * [Compare hourly to daily](#compare-hourly-to-daily)
* [Resources](#resources)
* [References](#references)

<!-- vim-markdown-toc -->


---
> **Not thoroughly reviewed !**

> Many of the data-preparation and comparison steps shown here are also available
as reusable [Miller](https://miller.org) scripts in
[`scripts/miller/`](../scripts/miller/)
(see [Resources](#resources)).

---

## In short

### The challenge

The goal is to estimate
the **hourly electricity generation by technology** for Switzerland 
in a consistent way.

---

> From [https://www.energydatahackdays.ch/challenges/estimating-hourly-energy-production-for-switzerland](https://www.energydatahackdays.ch/challenges/estimating-hourly-energy-production-for-switzerland)

>*The Swiss Federal Office of Energy currently publishes electricity production
data on a daily level across multiple technologies such as hydro, nuclear,
thermal, wind and PV. However, with the increasing share of renewable and
variable energy sources, hourly resolution becomes crucial to better understand
system dynamics. While hourly production data is available from the ENTSO-E
Transparency Platform, it is not directly aligned with the official daily
totals published by the SFOE.*
>
> *The goal of this challenge is to ***combine these
data sources and develop a method to estimate hourly electricity production per
technology in a consistent way***. Participants will explore how ENTSO-E hourly
profiles can be scaled or adjusted to match SFOE's daily totals. The challenge
is to ensure that the resulting time series is both physically plausible and
methodologically transparent.*

---

### Importance

- Policy and LCA applications need **hourly mix and emissions**, not just annual or daily averages.

- See also : https://en.wikipedia.org/wiki/Electricity_sector_in_Switzerland


### The problem

- The Swiss Federal Office for Energy (SFOE)
publishes **reliable**  **daily** energy production time series by technology,
however not **complete hourly breakdowns**.

- The European Network of Transmission System Operators for Electricity (ENTSO-E)
transparency platform (and Swissgrid ?) provide **hourly data**,
but with **different categorizations**, **gaps**, **revisions**,
and cross‑border trades
that make them incompatible with SFOE aggregates “as is”.

---
See also : 

> Methodology on the EnergieTakt Karte [^EnergieTakt]

> CH: The Swiss electricity generation data published via ENTSO-E 
> covers _only large power plants_ with an installed capacity of `>100` MW.
> Smaller power plants are not included.
> In addition to the ENTSO-E data,
> the Swiss TSO (Swissgrid) publishes quarter-hourly data on total generation
> as well as final and total consumption for Switzerland [3],
> and their subsidiary Pronovo publishes a very detailed quarter-hourly breakdown of renewable generation [4].
> These data are not provided in realtime but
> typically around the 15th of each month for the prior month.
> Using the datasets by Swissgrid and Pronovo,
> we calculate an estimate for the remaining unreported generation.
> By comparison with aggregated data from other sources (e.g. SFOE),
> we concluded that _the remaining generation is mainly from small hydro power plants_.
> Therefore, we classify it under ‘Hydro’.
> Furthermore, the difference between final and total consumption in the Swissgrid dataset
> is utilized to estimate the energy consumed by hydro pumped storage charging.
> Herein, we account for a 6% share to represent grid losses and in-house consumption by power plants.

[^EnergieTakt]: https://www.energietakt.com/methodology-of-the-energietakt-karte

---

### Task & Requirements

Estimate physically plausible and consistent high-frequency (hourly) profiles
of electricity generation in a methodologically transpaent way.

The new hourly time series should :

- base their intra-day shape on the ENTSO-E high-frequency hourly electricity generation profiles
- are consistent with the magnitude/level of the official SFOE daily totals by technology
- align with physical and statistical constraints
- are non‑negative, feature plausible ramps, (and... water balance for hydro)
- build with open code and reproducible pipelines
- are supported by clear documentation of assumptions and uncertainty.


## Data

### SFOE daily time series

SFOE provides the most trustworthy Swiss reference data
(closer to the statistical truth)
on energy production and consumption,
however at a **lower frequency**.[^3]

  - daily or monthly electricity generation by technology :
    - Hydro : run‑of‑river, reservoir
    - Nuclear
    - Solar
    - Wind
    - Fossil Gas

**Sources**

- https://opendata.swiss/fr/dataset/schweizerische-statistik-der-erneuerbaren-energien
- https://opendata.swiss/fr/dataset/schweizerische-gesamtenergiestatistik
- https://opendata.swiss/en/dataset/energiedashboard-ch-stromproduktion-swissgrid
- https://opendata.swiss/en/dataset/energiedashboard-ch-stromproduktion-swissgrid/resource/0879ba1b-40ea-4e26-bba0-9cbb339f577e
- https://www.bfe.admin.ch/bfe/en/home/supply/statistics-and-geodata/energy-statistics.html

#### Understand the SFOE data

> Source : https://www.energiedashboard.admin.ch/strom/produktion

The _power production_ figures available through SFOE's
(Swiss Federal Office of Energy) energy dashboard 
(across multiple technologies such as hydro, nuclear, thermal, wind and PV)
are reportedly aggregated **daily** data.[^0]
The data are publicly accessible via [opendata.swiss](https://opendata.swiss/en/dataset/energiedashboard-ch-stromproduktion-swissgrid) [^1][^2]
in the form of comma-separated-values[^3].
The _provider_ of the data, however, is Swissgrid.[^4]  Read on the next
subsection about the _raw_ time series.

#### Download

##### CSV data

We download the daily _SFOE_ time series :

[energiedashboard.ch: Stromproduktion Swissgrid-CSV](https://opendata.swiss/en/dataset/energiedashboard-ch-stromproduktion-swissgrid/resource/0879ba1b-40ea-4e26-bba0-9cbb339f577e)

and have a quick-look on the downloaded data

``` bash
mlr --csv head -n 3 ogd104_stromproduktion_swissgrid.csv
```

returns

``` csv
Datum,Energietraeger,Produktion_GWh
2015-01-01,Flusskraft,22.6
2015-01-01,Kernkraft,79.6
2015-01-01,Photovoltaik,1.2
```

##### JSON data via the Web API

---
Input : `https://energiedashboard.ch/api/v1/datasets/stromproduktion-swissgrid/data?from=2026-01-01&offset=0&limit=1000'`  
Output `stromproduktion.csv`

---

###### Get JSON data 

Following, let's retrieve **daily electricity production** totals for 2026

``` bash
curl -s -X 'GET'   'https://energiedashboard.ch/api/v1/datasets/stromproduktion-swissgrid/data?from=2026-01-01&offset=0&limit=1000'   -H 'accept: application/json'   > stromproduktion.json
```

and take a look at

``` bash
mlr --ijson head stromproduktion.json
```

_This will return a large one-liner_ :

`data.1.datum=2026-03-13,data.1.energietraeger=Thermische,data.1.produktion_gwh=8.6,...`

###### Convert JSON to CSV

Now, convert `stromproduktion.json` to CSV (new file named `stromproduktion.csv`) : 

``` bash
mlr --ijson put '
  for (k,v in $data) {
    @row = v;
    emit @row
  }
' then cut -f datum,energietraeger,produktion_gwh \
then rename 'produktion_gwh,Produktion_GWh' \
--ocsv \
then skip-trivial-records \
stromproduktion.json \
> stromproduktion.csv
```


#### Verify integrity ?

---
Input : `stromproduktion.csv`, `ogd104_stromproduktion_swissgrid.csv`  
Output : -

---

We _compare_ the Web-API retrieved data
`stromproduktion.csv`
to the manually downloaded sample data
`ogd104_stromproduktion_swissgrid.csv`,
to ensure we have the same numbers,
i.e. no errors during the JSON

``` bash
mlr --csv \
stats1 -a sum -f Produktion_GWh  -g energietraeger \
then sort -f energietraeger \
stromproduktion.csv
```

returns

``` csv
energietraeger,Produktion_GWh_sum
Flusskraft,3268.4999999999995
Kernkraft,5864.4
Photovoltaik,2332.6999999999994
Speicherkraft,5773.400000000004
Thermische,1152.100000000001
Wind,57.30000000000002
```

and

``` bash
mlr --csv \
filter '$Datum =~ "2026"' \
then stats1 -a sum -f Produktion_GWh -g Energietraeger \
then sort -f Energietraeger \
ogd104_stromproduktion_swissgrid.csv
```

returns

```
Energietraeger,Produktion_GWh_sum
Flusskraft,3268.5000000000005
Kernkraft,5864.400000000002
Photovoltaik,2332.7
Speicherkraft,5773.399999999997
Thermische,1152.1000000000004
Wind,57.300000000000004
```

#### Work with a sample ?

> ___Skip this section if working with a small sample is not of concern.___

---
Input : `stromproduktion.csv`  
Intermediate : `stromproduktion_2026_01.csv`  
Output : `stromproduktion_2026_01_GWh.csv`

---

For practical reasons, we can work with a smaller sample,
i.e. the January 2026 data.

``` bash
mlr --csv \
sort -f datum \
then filter '$datum =~ "2026-01"' \
stromproduktion.csv \
> stromproduktion_2026_01.csv
```

Actually save output to a new file

``` bash
mlr --csv \
stats1 -a sum -f Produktion_GWh  -g energietraeger \
then sort -f energietraeger \
then label Type,Production_GWh \
stromproduktion_2026_01.csv  
> stromproduktion_2026_01_GWh.csv
```

#### Convert to wide table

``` bash
mlr --csv \
sort -f datum,energietraeger \
then nest --implode --values --across-fields -f energietraeger \
stromproduktion.csv \
| mlr --csv rename datum,Date \
then reshape -s energietraeger,Produktion_GWh \
> stromproduktion_wide.csv
```

---
### Swissgrid

Swiss TSO data[^Swissgrid]

Swissgrid :

- is the electricity grid operator in Switzerland
- publishes total **hourly** (even **quarter-hourly**) electricity production
  (including consumption, load, and imports/exports)
- is source for SFOE's daily time series
  > _though Swissgrid is not mentioned in the Challenge_ !


The quarter-hourly/hourly time series can be used to verify totals.
Unfortunately, this data :

  - is not real-time
  - is not separated in production categories
  
[^Swissgrid]: https://www.swissgrid.ch/en/home/operation/grid-data/generation.html

#### Understand the Swissgrid data

The _raw_ time series for the daily aggregated data come from Swissgrid :

> Description from
[www.swissgrid.ch/en/home/operation/grid-data/generation.html#downloads](https://www.swissgrid.ch/en/home/operation/grid-data/generation.html#downloads)

> The total of the produced energy in the control block Switzerland.
> The aggregations of the feed-in sequences for the balancing groups
> are sent from the distribution network operators to Swissgrid.
> The sum contains all the energy produced and fed in the network.
> (Only productions plants equipped with load profile meters)

Looking closer at the _raw_ time series provided by Swissgrid
in form of Excel spreadsheets [^5]
their _original_ temporal resolution is **every 15'**[^6].

##### Sample statistics

Example statistics from the 2026 Swissgrid data (downloaded on April 21)
after manually extracting the energy production time series
from the _Zeitreihen0h15_ sheet
(starting from `01.01.2026 00:00` up to `31.03.2026 23:45`,
here saved as : `total_energy_production_swissgrid.csv`) :

``` bash
mlr --c2p --ofmt '%.2f' \
put '$MWh = $kWh / 1000' \
then stats1 -a sum,median,mean,stddev,mad -f MWh \
total_energy_production_swissgrid.csv

MWh_sum     MWh_median MWh_mean MWh_stddev MWh_mad
13100359.20 1375.90    1516.95  573.90     471.09
```

---
### ENTSO‑E hourly time series

The ENTSO-E transparency platform provides :

- high-frequency hourly time series by production type
- misses part of the system, especially depending on technology[^4][^1],
  thus are incomplete or inconsistent [^1][^2][^3][^electricitymaps-issue-892] :
  - _"..there are a lot of small hydro plants in
    Switzerland[^cleantech_small-scale-hydropower-in-switzerland] with a
    complicated ownership structure.."_
  - Hydro & Hydro storage: On average, two third of the total annual output
    is missing (13.5TWh vs. 36.3 TWh actual cumulated in 2016)
  - Non-nuclear thermal: 100% is missing. (0 vs. 3.1TWh actual in 2016)
  - e.g. for _Run-of-river_ less than 2 of the 17.7 TWh are included in the
      ENTSOE values. This was confirmed by the energy specialists in our team.
      Switzerland has a lot of small run-of-river plants that are so small that
      they do not have to report live data, so that this data is not
      available.[^electricitymaps-issue-2898]
  - Conventional thermal is the other production category that is missing in
      the data.[^electricitymaps-issue-2898]

[^cleantech_small-scale-hydropower-in-switzerland]: https://www.cleantech-alps.com/wp-content/uploads/2023/11/cleantech_small-scale-hydropower-in-switzerland.pdf
[^electricitymaps-issue-892]: https://github.com/electricitymaps/electricitymaps-contrib/issues/892
[^electricitymaps-issue-2898]: https://github.com/electricitymaps/electricitymaps-contrib/pull/2898


#### Understand the ENTSO-E data

[...]

> ENTSO-E : European Network of Transmission System Operators for Electricity

#### Manual download

The full directory of the ENTSO-E data
can be downloaded manually
from the **File Library** of the Transparency Platform :

**File Browser Mode** > **TP_export** > `AggregatedGenerationPerType_16.1.B_C_r3`

These files are (TSV and not CSV, yet they are)
consistent in terms of their header,
i.e. the data-columns are :

``` bash
DateTime(UTC)
ResolutionCode
AreaCode
AreaDisplayNameAreaTypeCode
AreaMapCode
ProductionType
ActualGenerationOutput[MW]
ActualConsumption[MW]
UpdateTime(UTC)
```

In addition, the timestamps are all in UTC.
While the downloaded `.zip` file
(which is the complete folder with monthly time series per file)
is larg (~690MB) and needs some filtering to extract data for Switzerland.

> * This dataset is perhaps cleaner than files downloaded via the interactive map
@ [https://transparency.entsoe.eu/generation/actual/perType/generation?appState=%7B%22sa%22%3A%5B%22BZN%7C10YGR-HTSO-----Y%22%5D%2C%22st%22%3A%22BZN%22%2C%22mm%22%3Atrue%2C%22ma%22%3Afalse%2C%22sp%22%3A%22HALF%22%2C%22dt%22%3A%22CHART%22%2C%22df%22%3A%5B%222026-04-30%22%2C%222026-04-30%22%5D%2C%22tz%22%3A%22UTC%22%7D](https://transparency.entsoe.eu/generation/actual/perType/generation?appState=%7B%22sa%22%3A%5B%22BZN%7C10YGR-HTSO-----Y%22%5D%2C%22st%22%3A%22BZN%22%2C%22mm%22%3Atrue%2C%22ma%22%3Afalse%2C%22sp%22%3A%22HALF%22%2C%22dt%22%3A%22CHART%22%2C%22df%22%3A%5B%222026-04-30%22%2C%222026-04-30%22%5D%2C%22tz%22%3A%22UTC%22%7D).

Some metadata for `AggregatedGenerationPerType_16.1.B_C_r3` are available at

[Transparency Platform > Specifications > File Library extracts > AggregatedGenerationPerType-16-1-B-C-r3](https://transparencyplatform.zendesk.com/hc/en-us/articles/36493702227729-AggregatedGenerationPerType-16-1-B-C-r3)

---
##### Other sources ?

- [ENTSO-E Hydropower modelling data (PECD) in CSV format](https://zenodo.org/records/3985078) [^DeFelice2020]

[^DeFelice2020]: De Felice, Matteo. “ENTSO-E Hydropower Modelling Data (PECD) in CSV Format”. Zenodo, August 14, 2020. https://doi.org/10.5281/zenodo.3985078.

---
Input : `2026_01_AggregatedGenerationPerType_16.1.B_C_r3_AreaMapCode.csv`  
Intermediate : `2026_01_AggregatedGenerationPerType_16.1.B_C_r3_AreaMapCode_CH_GWh.csv`  
Output : `entsoe_GWh.csv`

---

#### Extract data for Switzerland

```
mlr --t2c \
filter '$AreaMapCode == "CH"' \
then sort -f "DateTime(UTC)" \
*_AggregatedGenerationPerType_16.1.B_C_r3.csv \
> AggregatedGenerationPerType_16.1.B_C_r3_CH.csv
```

#### Convert MWh to GWh

and convert units to GWh while keeping only the columns : 
`DateTime(UTC)`, `ProductionType` and `Generation_GWh`

``` bash
mlr --csv \
put '$Generation_GWh = ${ActualGenerationOutput[MW]} / 1000'  \
then cut -f "DateTime(UTC)",ProductionType,Generation_GWh \
then rename "DateTime(UTC),DateTime,ProductionType,Type"  \
AggregatedGenerationPerType_16.1.B_C_r3_CH.csv \
> entsoe_aggregated_generation_per_type_GWh.csv
```

#### Convert to wide table

##### Diagnose the data structure

First we take a look at the uniue _types_ and their _counts_

``` bash
mlr --csv uniq -c -f Type entsoe_aggregated_generation_per_type_GWh.csv
```
```
Type,count
Solar,99286
Wind Onshore,99262
Fossil Gas,6215
Nuclear,95013
Hydro Pumped Storage,94941
Hydro Water Reservoir,94941
Hydro Run-of-river and poundage,92206
```

The *problem* is that the ENTSO-E time series are sparse.
The counts show that not every `DateTime` has data for every `Type`
(e.g., Solar appears 99k times vs. Fossil Gas only 6k).
In other words, the *problem* is that the ENTSO-E time series are sparse.
What is required, however, is a standard CSV with all types as columns,
even where data is absent.

---

> Three main types of hydropower plants (HPP) are distinguished:
> - Storage HPP with at least one headwater reservoir allowing for flexible production according to the variations of the demand and the production from other sources,
> - Run-of-river HPP (without appreciable storage) whose production directly depends on the inflows, and
> - Pumped storage plants (PSP) which allow to store large amounts of electric energy by using surplus energy for pumping and releasing energy in times of high demand.

> Source : [Swiss Potential for Hydropower Generation and Storage](https://ethz.ch/content/dam/ethz/special-interest/baug/department/news/dokumente/Hydropower_Synthesis_Report_sm.pdf) [^Boes2021]

[^Boes2021]: Boes, R., Hohermuth, B., Giardini, D. (eds.), Avellan, F., Boes, R, Burlando, P., Evers, F., Felix, D., Hohermuth, B., Manso, P., Münch-Aligné, C., Schmid, M., Stähli, M., Weigt, H. (2021): Swiss Potential for Hydropower Generation and Storage, Synthesis Report, ETH Zurich, 2021.

---

##### Unsparsify the data

A `nest` operation will create varying field sets per row
(e.g. `DateTime,Solar` vs `DateTime,Fossil Gas,Solar`),
breaking the CSV's schema consistency.
The solution is to `unsparsify` the data after `nest` (or after `reshape`)
to fill missing fields with empty strings,
creating a consistent schema across all rows.

##### Reshape to wide table

``` bash
mlr --csv \
sort -f DateTime,Type \
then nest --implode --values --across-fields -f Type entsoe_aggregated_generation_per_type_GWh.csv \
| mlr --csv \
reshape -s Type,Generation_GWh \
then unsparsify \
> entsoe_hourly_generation_per_type.csv
```

> **How it works**
>
> Miller streams data record after record.
> Hence, we can `nest`, then `reshape` and finally `unsparsify`
> which will process each row to ensure internal consistency.
>
> - `nest --implode --values --across-fields -f Type` : pivots types into columns per DateTime, but sparsely.
> - `unsparsify` : adds missing type columns so every row has identical `Type` fields (`Solar`, `Wind Onshore`, etc.).
> - `reshape -s Type,Generation_GWh` sees stable input headers and outputs pivoted DateTime rows with Solar_Generation_GWh, Wind Onshore_Generation_GWh, etc..

Finally, our reshaped time series look as follows
(showing 3 lines from the `head` and `tail` of the data) : 

``` bash
mlr --c2m head -n 3 entsoe_hourly_generation_per_type.csv
```
| DateTime            | Solar                   | Wind Onshore | Fossil Gas | Nuclear | Hydro Pumped Storage | Hydro Water Reservoir | Hydro Run-of-river and poundage |
| ---                 | ---                     | ---          | ---        | ---     | ---                  | ---                   | ---                             |
| 2014-12-30 23:00:00 | 0.000029999999999999997 |              |            |         |                      |                       |                                 |
| 2014-12-31 00:00:00 | 0.00005                 |              |            |         |                      |                       |                                 |
| 2014-12-31 01:00:00 | 0.00007000000000000001  |              |            |         |                      |                       |                                 |



``` bash
mlr --c2m tail -n 3 entsoe_hourly_generation_per_type.csv
```
| DateTime | Solar | Wind Onshore | Fossil Gas | Nuclear | Hydro Pumped Storage | Hydro Water Reservoir | Hydro Run-of-river and poundage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-04-29 17:00:00 | 0.379468231 | 0.027049998999999998 |  | 2.5298000000000003 | 3.2977 | 2.31515 | 1.7917299800000002 |
| 2026-04-29 18:00:00 | 0.032936542000000006 | 0.0287 |  | 2.5335199999999998 | 3.54215 | 2.37668 | 1.794550048 |
| 2026-04-29 19:00:00 | 0 | 0.030600000000000002 |  |  |  |  | 1.7973499750000002 |


---
### Compare time series

#### SFOE vs Swissgrid

We compare the total production for a few months given by the SFOE daily series

``` bash
mlr --csv \
filter 'strptime($Datum, "%Y-%m-%d") >= strptime("2026-01-01", "%Y-%m-%d") && strptime($Datum, "%Y-%m-%d") <= strptime("2026-03-31", "%Y-%m-%d")' \
then stats1 -a sum -f Produktion_GWh data/SFOE/ogd104_stromproduktion_swissgrid.csv
```
```
Produktion_GWh_sum
14148.000000000005
```
and the ... by Swissgrid

``` bash
mlr --csv \
cut -f "Summe produzierte Energie Regelblock Schweiz Total energy production Swiss controlblock - kWh" \
then label "Production kWh" \
then put '${Production GWh} = ${Production kWh} / 1000000' \
then stats1 -a sum -f "Production GWh" \
data/clean/EnergieUebersichtCH-2026_production_wide.csv
```
```
Production GWh_sum
13100.35919622985
```

Even here the differene is large,
which implies the lack of a common system to report to, collect and
harmonise data on the generation of electricity at a national level.

#### SFOE vs ENTSOE

##### Link SFOE and ENTSO-E data

Part of the preparative steps
is to understand the correspondence between definitions of energy generation types
in the SFOE and ENTSO-E time series.


##### Electricity generation types

The electricity generation types in 

- the _daily_ SFOE time series are :

    ```bash
    mlr --csv uniq -f Energietraeger ogd104_stromproduktion_swissgrid.csv
    ```
    ```
    Energietraeger
    Flusskraft
    Kernkraft
    Photovoltaik
    Speicherkraft
    Thermische
    Wind
    ```

- the _hourly_ ENTSO-E time series are :

    ``` bash
    mlr --csv sort -f Type then uniq -f Type entsoe_aggregated_generation_per_type_GWh.csv
    ```
    ```
    Type
    Fossil Gas
    Hydro Pumped Storage
    Hydro Run-of-river and poundage
    Hydro Water Reservoir
    Nuclear
    Solar
    Wind Onshore
    ```

##### Mapping ENTSO-E to SFOE types

Mapping the ENTSO-E _types_ to the SFOE ones in one table :

<!-- layed out in the column `Produktion_GWh` by SFOE to ENTSO-E _Production Type_ -->


| ENTSO-E                         | SFOE          |
|---------------------------------|---------------|
| Fossil Gas                      | Thermische    |
| Hydro Pumped Storage            | Speicherkraft |
| Hydro Run-of-river and poundage | Flusskraft    |
| Hydro Water Reservoir           | Speicherkraft |
| Nuclear                         | Kernkraft     |
| Solar                           | Photovoltaik  |
| Wind Onshore                    | Wind          |



| SFOE                 | ENTSO‑E                                                                   | Notes / caveats                                                                                                  |
| -------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------                      |
| Flusskraft           | Hydro Run-of-river and poundage                                           | Conceptually run‑of‑river; ENTSO-E may miss small plants not reported                                            |
| Speicherkraft        | Hydro Water Reservoir; Hydro Pumped Storage (gen.)                        | Storage + pumped storage generation; pumping consumption appears as load                                         |
| Wasserkraft total    | All three hydro types above                                               | ENTSO‑E for CH only covers plants ≥100 MW; small/er hydro missing [^energietakt+1]                               |
| Kernenergie          | Nuclear                                                                   | One‑to‑one correspondence                                                                                        |
| Fossil / thermisch   | Fossil Brown coal; Fossil Hard coal; Fossil Gas; Fossil Oil; Other fossil | ENTSO‑E CH data historically incomplete for non‑nuclear, thermal [^https://github.com/SaM-92/energy-data-entsoe] |
| Solar (Photovoltaik) | Solar                                                                     | PV mostly aligned between SFOE, Pronovo, ENTSO‑E; check small‑scale coverage. [^energietakt+1]                   |
| Windkraft            | Wind Onshore (and Offshore if any)                                        | Switzerland essentially only onshore                                                                             |
| Übrige erneuerbare   | Biomass; Geothermal; Other renewable                                      | Depends on SFOE grouping for "other renewables"                                                                  |


[^energietakt+1]: https://www.energietakt.com/methodology-of-the-energietakt-karte/

> **Assumptions**
>
> SFOE Flusskraft + Speicherkraft ≈ sum of ENTSO‑E hydro types, _after correcting for small‑plant under‑coverage_.
> Flusskraft ≈ ENTSO‑E Run‑of‑river and poundage
> Speicherkraft ≈ Reservoir + Pumped Storage

and applying this mapping with Miller's help

``` bash
mlr --csv put '
  begin {
    @map["Fossil Gas"] = "Thermische";
    @map["Hydro Pumped Storage"] = "Speicherkraft";
    @map["Hydro Run-of-river and poundage"] = "Flusskraft";
    @map["Hydro Water Reservoir"] = "Speicherkraft";
    @map["Nuclear"] = "Kernkraft";
    @map["Solar"] = "Photovoltaik";
    @map["Wind Onshore"] = "Wind"
  }
  $MatchType = @map[$Type]
' \
entsoe_aggregated_generation_per_type_GWh.csv \
> entsoe_aggregated_generation_per_type_mapping_to_sfoe_GWh.csv`
```

``` bash
mlr --csv \
filter 'strptime($DateTime, "%Y-%m-%d %H:%M:%S") >= strptime("2015-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")' \
entsoe_aggregated_generation_per_type_mapping_to_SFOE_GWh.csv \
> entsoe_hourly_generation_per_type_mapping_to_SFOE_GWh.csv
```

Print to verify output

``` bash
mlr --c2p --ofmt '%.2f' cat entsoe_GWh.csv
```

```
Type                            Production_GWh MatchType
Hydro Pumped Storage            750.07         Speicherkraft
Hydro Run-of-river and poundage 661.77         Flusskraft
Hydro Water Reservoir           992.96         Speicherkraft
Nuclear                         1458.41        Kernkraft
Solar                           78.36          Photovoltaik
Wind Onshore                    17.99          Wind
```

Now we can compare the _daily_ (SFOE) and _hourly_ (ENTSO-E) time series
and verify they refer to the same quantities.

Let's generate a file for all production types (?)

``` bash
mlr --csv \
join --lp Daily_ --rp Hourly_ -j Type -r MatchType -f stromproduktion_2026_01_GWh.csv entsoe_GWh.csv \
|mlr --csv reorder -f Type,Hourly_Type,Daily_Production_GWh,Hourly_Production_GWh \
then rename Type,SFOE_Type,Hourly_Type,ENTSOE_Type \
then put '
  $Difference = $Daily_Production_GWh - $Hourly_Production_GWh;
  $Percentage = ($Daily_Production_GWh == 0 ? 0 : 100 * $Difference / $Daily_Production_GWh)
' \
> type_and_production.csv
```

Now pretty-print via `--c2p`

``` bash
mlr --c2p cat type_and_production.csv
```

returns

```
SFOE_Type     ENTSOE_Type                     Daily_Production_GWh Hourly_Production_GWh Difference           Percentage
Speicherkraft Hydro Pumped Storage            2177.1000000000004   750.0662699999997     1427.0337300000006   65.54745900509853
Flusskraft    Hydro Run-of-river and poundage 706.0999999999999    661.7663986239978     44.33360137600209    6.278657608837573
Speicherkraft Hydro Water Reservoir           2177.1000000000004   992.9575699999995     1184.1424300000008   54.390814845436616
Kernkraft     Nuclear                         1454.1000000000001   1458.4139899999996    -4.313989999999421   -0.2966776700364088
Photovoltaik  Solar                           205.89999999999998   78.35501765500003     127.54498234499995   61.945110415250106
Wind          Wind Onshore                    17.999999999999996   17.98906078800001     0.010939211999986043 0.06077339999992247
```

or in Markdown and figures limited to two decimal digits

``` bash
mlr --csv --omd --ofmt '%.2f' cat type_and_production.csv
```

| SFOE_Type | ENTSOE_Type | Daily_Production_GWh | Hourly_Production_GWh | Difference | Percentage |
| --- | --- | --- | --- | --- | --- |
| Speicherkraft | Hydro Pumped Storage | 2177.10 | 750.07 | 1427.03 | 65.55 |
| Flusskraft | Hydro Run-of-river and poundage | 706.10 | 661.77 | 44.33 | 6.28 |
| Speicherkraft | Hydro Water Reservoir | 2177.10 | 992.96 | 1184.14 | 54.39 |
| Kernkraft | Nuclear | 1454.10 | 1458.41 | -4.31 | -0.30 |
| Photovoltaik | Solar | 205.90 | 78.36 | 127.54 | 61.95 |
| Wind | Wind Onshore | 18.00 | 17.99 | 0.01 | 0.06 |



##### Combining Speicherkraft types

Two of the _Hydro_ types among the ENTSOE classification _belong_ to SFOE's
_Speicherkraft_ !  Let's try to combine them.

###### "Speicherkraft" production

---
Input : `type_and_production.csv`  
Output : `type_and_production_Speicherkraft_Hourly_Production.csv`

---

Generate the data

``` bash
mlr --csv filter '$SFOE_Type == "Speicherkraft"' \
then stats1 -a sum -f Hourly_Production_GWh -g SFOE_Type \
then put '$ENTSOE_Type = "Hydro: Pumped Storage + Water Reservoir"' \
then reorder -f SFOE_Type,ENTSOE_Type \
type_and_production.csv \
> type_and_production_Speicherkraft_Hourly_Production.csv

```

and print via

``` bash
mlr --c2p --ofmt '%.2f' cat type_and_production_Speicherkraft_Hourly_Production.csv
```

which returns

```
SFOE_Type     ENTSOE_Type                             Hourly_Production_GWh_sum
Speicherkraft Hydro: Pumped Storage + Water Reservoir 1743.02
```


###### Production without "Speicherkraft"

---
Input : `type_and_production.csv`  
Output : `type_and_production_without_Speicherkraft`

---

Generate the wanted CSV file

``` bash
mlr --csv filter '$SFOE_Type != "Speicherkraft"' \
type_and_production.csv \
> type_and_production_without_Speicherkraft.csv
```

and print via

``` bash
mlr --c2p --ofmt '%.2f' cat type_and_production_without_Speicherkraft.csv
```

returns

```
SFOE_Type    ENTSOE_Type                     Daily_Production_GWh Hourly_Production_GWh Difference Percentage
Flusskraft   Hydro Run-of-river and poundage 706.10               661.77                44.33      6.28
Kernkraft    Nuclear                         1454.10              1458.41               -4.31      -0.30
Photovoltaik Solar                           205.90               78.36                 127.54     61.95
Wind         Wind Onshore                    18.00                17.99                 0.01       0.06
```


###### Restore lost field `DailyProduction_GWh`

---
Input :  `type_and_production.csv`, `type_and_production_Speicherkraft_Hourly_Production.csv`  
Output : `type_and_production_only_Speicherkraft.csv`

---

After the `stats1 -a sum` command, not all _fields_ are preserved.
Hence, we need to get the `DailyProduction_GWh` column back in manually !

Genrate a "join"ed CSV file

``` bash
mlr --csv then join --lk "Daily_Production_GWh" -j SFOE_Type -f type_and_production.csv type_and_production_Speicherkraft_Hourly_Production.csv \
| mlr --csv head -n 1   then put '
  $Difference = $Daily_Production_GWh - $Hourly_Production_GWh_sum;
  $Percentage = ($Daily_Production_GWh == 0 ? 0 : 100 * $Difference / $Daily_Production_GWh)
'
then rename Hourly_Production_GWh_sum,Hourly_Production_GWh
then reorder -f SFOE_Type,ENTSOE_Type > type_and_production_only_Speicherkraft.csv
```

and print

``` bash
mlr --c2p --ofmt '%.2f' cat type_and_production_only_Speicherkraft.csv
```

```
SFOE_Type     ENTSOE_Type                             Daily_Production_GWh Hourly_Production_GWh Difference Percentage
Speicherkraft Hydro: Pumped Storage + Water Reservoir 2177.10              1743.02               434.08     19.94
```


##### Combine in one data file

---
Input :  `type_and_production_without_Speicherkraft.csv`, `type_and_production_only_Speicherkraft.csv`  
Output : `type_and_production_harmonised.csv`

---

Generate the "final" CSV file `type_and_production_harmonised.csv`

``` bash
mlr --csv cat \
then sort -f SFOE_Type \
type_and_production_without_Speicherkraft.csv \
type_and_production_only_Speicherkraft.csv \
> type_and_production_harmonised.csv
```

and print it

``` bash
mlr --c2p --ofmt '%.2f' --omd cat type_and_production_harmonised.csv
```


| SFOE_Type | ENTSOE_Type | Daily_Production_GWh | Hourly_Production_GWh | Difference | Percentage |
| --- | --- | --- | --- | --- | --- |
| Flusskraft | Hydro Run-of-river and poundage | 706.10 | 661.77 | 44.33 | 6.28 |
| Kernkraft | Nuclear | 1454.10 | 1458.41 | -4.31 | -0.30 |
| Photovoltaik | Solar | 205.90 | 78.36 | 127.54 | 61.95 |
| Speicherkraft | Hydro: Pumped Storage + Water Reservoir | 2177.10 | 1743.02 | 434.08 | 19.94 |
| Wind | Wind Onshore | 18.00 | 17.99 | 0.01 | 0.06 |


##### Compare hourly to daily

The daily time series from SFOE is the "truth" reference.
Let's aggregate the ENTSO-E data from hourly to daily and compare the sums for
each type.

```
mlr --c2p cat entsoe_generation_per_type_2026_01_daily.csv
```

```
Date       Hydro Pumped Storage Hydro Run-of-river and poundage Hydro Water Reservoir Nuclear            Solar              Wind Onshore
2026-01-01 3364.59              17817.699941999996              7708.32               47089.79           4334.332181        809.929896
2026-01-02 5767.000000000001    16765.           9181.329999999998     47057.68           2157.0237300000003 835.6943990000001
2026-01-03 4405.989999999999    16534.200003                    8222.769999999999     47116.420000000006 1448.9675039999997 336.28556
2026-01-04 6638.249999999999    16698.60009                     17522.770000000004    47140.840000000004 2172.514831        86.41189899999998
2026-01-05 60718.909999999996   22843.999988999993              53405.200000000004    47120.87           1870.561648        120.863572
2026-01-06 56087.40999999999    27350.799919                    50029.22000000001     47094.479999999996 1616.3419540000002 213.361304
2026-01-07 30120.04             23420.299855999994              46964.119999999995    47110.25           2102.470898        359.892285
2026-01-08 44120.80000000001    23280.199937999994              48335.56              47055.890000000014 422.90077800000006 1089.8525180000001
2026-01-09 22028.450000000004   23210.400134999996              42649.78              46973.30000000001  1826.078797        1485.296912
2026-01-10 7016.81              19438.700062                    29296.450000000004    47132.109999999986 683.1590229999999  1265.784486
2026-01-11 3783.9500000000003   16124.299976000002              14172.650000000001    47131.86           898.9946060000001  261.491615
2026-01-12 41023.02             23222.799917                    50930.47000000001     47096.33999999999  1182.845463        1033.4175199999997
2026-01-13 38940.530000000006   26009.400015                    47424.22              47081.29           2445.7513239999994 1258.316618
2026-01-14 28744.740000000005   24210.799981999993              38730.85              47084.67000000001  3670.4754300000004 971.398285
2026-01-15 23051.979999999996   23645.100026999997              43010.15              47040.020000000004 4091.0804479999997 953.1150900000001
2026-01-16 26073.37             23545.899831                    40248.17              47131.549999999996 3504.919617        686.065091
2026-01-17 7527.529999999999    18103.600087999996              15556.849999999999    47121.77           2863.6410240000005 652.54321
2026-01-18 4674.650000000001    17066.500052000003              10247.560000000001    45454.64000000001  2187.598179        558.7421949999999
2026-01-19 22622.56             19553.599904                    31411.799999999996    47113.81999999999  3057.303321        384.55628800000005
2026-01-20 27648.12             22053.39994999999               37478.469999999994    47122.75000000001  3933.6287360000006 500.9403669999999
2026-01-21 38882.98             22667.000113                    46655.63              47121.369999999995 4301.053486000001  264.875465
2026-01-22 40052.51999999999    25291.299432                    47194.689999999995    47110.170000000006 3322.544314        150.868214
2026-01-23 40169.95999999999    24525.200125000003              45463.319999999985    47121.01           2927.958388000001  408.9926619999999
2026-01-24 9192.789999999999    18983.699879999993              21237.210000000006    47117.61           2265.4737580000005 238.26938700000002
2026-01-25 2838.13              16474.000051                    11243.26              47122.990000000005 3195.3008729999997 146.67754599999998
2026-01-26 31901.600000000006   21702.500055000004              35646.97              47069.67           3405.375681000001  354.60200900000007
2026-01-27 27252.77             22463.799855999998              30939.2               47121.939999999995 3181.651645        1445.3218990000005
2026-01-28 29844.860000000004   23880.299913999992              35546.340000000004    47094.270000000004 1120.210531        192.409131
2026-01-29 38854.850000000006   24773.099598000004              36540.729999999996    47056.31999999999  3151.939854        176.44766099999998
2026-01-30 21895.329999999998   21747.49980399999               28706.78              47095.340000000004 1982.8857410000003 654.174176
2026-01-31 4821.78              18362.100029999998              11256.730000000001    47112.96           3030.033892000001  92.463528
```

## Resources

**Tools**
- [**tempdisagg**](https://d-nb.info/1219272752/34) — Chow-Lin, Denton temporal disaggregation (Python)
- [**miller** (`mlr`)](https://miller.org) — command-line CSV/JSON processing (used throughout this document)

**Pipeline scripts**
- Reusable scripts for the daily comparison and scaling-factor analysis live in `scripts/miller/`:
  - `join_SFOE_to_ENTSOE.sh` — join ENTSO-E daily and SFOE data on `Date`
  - `label_and_reorder.mlr` — label and reorder columns for side-by-side comparison
  - `derive_scaling_factors.sh` — compute daily scaling factors (SFOE / ENTSO-E)
  - `derive_scaling_factor_statistics.sh` — summarise scaling factor statistics

**Data access**
- [entoe-py / energy-data-entsoe](https://github.com/SaM-92/energy-data-entsoe) — ENTSO-E API wrappers and data download tools
- [ENTSO-E Hydropower modelling data (PECD)](https://zenodo.org/records/3985078) — Zenodo dataset

**Visualisation**
- [EnergieTakt map](https://www.energietakt.eu/karte/?region=DE&mode=EmissionsConsumption&scheme=DC&agg=Hourly&period=72h) — European electricity mix visualisation
- [Energy Charts (CH)](https://energy-charts.info/charts/power/chart.htm?l=en&c=CH) — Swiss power production charts

## References

[^0]: https://www.energiedashboard.admin.ch/strom/produktion
[^1]: https://opendata.swiss/en/dataset/energiedashboard-ch-stromproduktion-swissgrid
[^2]: https://opendata.swiss/en/dataset/energiedashboard-ch-stromproduktion-swissgrid/resource/0879ba1b-40ea-4e26-bba0-9cbb339f577e
[^3]: https://www.bfe-ogd.ch/ogd104_stromproduktion_swissgrid.csv
[^4]: https://www.swissgrid.ch/en/home/operation/grid-data/generation.html
[^5]: https://www.swissgrid.ch/en/home/operation/grid-data/generation.html#downloads
[^6]: Swissgrid energy overview Excel files available at [swissgrid.ch → generation downloads](https://www.swissgrid.ch/en/home/operation/grid-data/generation.html#downloads)
