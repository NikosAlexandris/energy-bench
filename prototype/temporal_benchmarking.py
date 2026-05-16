# from devtools import debug
from pathlib import Path
import pandas as pd
from pandas import Timestamp
import os
from tempdisagg import TempDisaggModel
from difference import plot_series_difference
from before_after import plot_series_before_and_after
from read import read_csv
from helpers import prepare_dataframe

#
START = Timestamp('2025-01-01')
END   = Timestamp('2025-01-31')  #12-31')

entsoe_csv = Path('data/ENTSOE/entsoe_hourly_generation_2015_2026.csv')
sfoe_csv = Path('data/SFOE/swissgrid_daily_production_2015_2026.csv')


# Create output dir
os.makedirs('output', exist_ok=True)

# Load datasets

entsoe_hourly = read_csv(
    source=entsoe_csv,
    start=START,
    end=END,
    time_column='DateTime',
)

sfoe_daily = read_csv(
    source=sfoe_csv,
    start=START,
    end=END,
    time_column='Date',  # Attention !
)
sfoe_daily = sfoe_daily.loc[START.normalize():END.normalize()]


# Aggregate ENTSO-E to daily for validation (GWh)
entsoe_hourly['Date'] = entsoe_hourly.index.normalize() # Ensure date-only
entsoe_daily = entsoe_hourly.groupby('Date').sum(numeric_only=True)
entsoe_daily['Hydro Total'] = (entsoe_daily['Hydro Run-of-river and poundage'] + 
                               entsoe_daily['Hydro Water Reservoir'] + 
                               entsoe_daily['Hydro Pumped Storage'])

# Prepare dataframes for TempDisaggModel (daily low-freq -> hourly high-freq)
# Hydro benchmarking
low_hydro = sfoe_daily[['Flusskraft', 'Speicherkraft']].sum(axis=1)
high_hydro = (entsoe_hourly['Hydro Run-of-river and poundage'] + 
              entsoe_hourly['Hydro Water Reservoir'] + 
              entsoe_hourly['Hydro Pumped Storage'])
df_hydro = prepare_dataframe(low_hydro, high_hydro)

model_hydro = TempDisaggModel(method='chow-lin', conversion='sum')
model_hydro.fit(df_hydro)

# hydro_benchmarked = pd.Series(model_hydro.predict().flatten(), name='hydro_benchmarked')
# hydro_benchmarked.to_csv('output/benchmarked_hourly_hydro.csv', index=False)

hydro_hourly_index = pd.date_range(START, periods=len(model_hydro.predict().flatten()), freq='h')

hydro_out = pd.DataFrame({
    'DateTime': hydro_hourly_index,
    'hydro_entsoe_original_gwh': high_hydro.reindex(hydro_hourly_index).values,
    'hydro_benchmarked_gwh': model_hydro.predict().flatten(),
})

hydro_out['date'] = hydro_out['DateTime'].dt.date
hydro_out['hour'] = hydro_out['DateTime'].dt.hour
hydro_out['month'] = hydro_out['DateTime'].dt.month
hydro_out['source_profile'] = 'ENTSO-E'
hydro_out['daily_target_source'] = 'SFOE'
hydro_out['variable'] = 'Hydro'

hydro_out.to_csv(
    'output/benchmarked_hourly_hydro.csv',
    index=False,
    date_format='%Y-%m-%d %H:%M:%S'
)


# Nuclear benchmarking
low_nuc = sfoe_daily['Kernkraft']
high_nuc = entsoe_hourly['Nuclear']
df_nuc = prepare_dataframe(low_nuc, high_nuc)

model_nuc = TempDisaggModel(method='chow-lin', conversion='sum')
model_nuc.fit(df_nuc)
# nuc_benchmarked = pd.Series(model_nuc.predict().flatten(), name='nuc_benchmarked')
# nuc_benchmarked.to_csv('output/benchmarked_hourly_nuclear.csv', index=False)
nuclear_hourly_index = pd.date_range(START, periods=len(model_nuc.predict().flatten()), freq='h')

nuc_out = pd.DataFrame({
    'DateTime': nuclear_hourly_index,
    'nuclear_entsoe_original_gwh': high_nuc.reindex(nuclear_hourly_index).values,
    'nuclear_benchmarked_gwh': model_nuc.predict().flatten(),
})

nuc_out['date'] = nuc_out['DateTime'].dt.date
nuc_out['hour'] = nuc_out['DateTime'].dt.hour
nuc_out['month'] = nuc_out['DateTime'].dt.month
nuc_out['source_profile'] = 'ENTSO-E'
nuc_out['daily_target_source'] = 'SFOE'
nuc_out['variable'] = 'Nuclear'

nuc_out.to_csv(
    'output/benchmarked_hourly_nuclear.csv',
    index=False,
    date_format='%Y-%m-%d %H:%M:%S'
)

# df_daily = pd.read_csv('output/benchmarked_hourly_hydro.csv', parse_dates=['DateTime'])
# df_daily = df_daily.set_index('DateTime')

# df_daily['GWh'] = pd.to_numeric(
#         df_daily['hydro_benchmarked_gwh'],
#         errors='coerce'
# )
# df_daily = df_daily.dropna(subset=['GWh'])
# df_daily.index = pd.date_range('2025-01-01', periods=len(df_daily), freq='h')

# df_daily['GWh'].resample('D').sum().plot(label='Benchmarked Daily')
# low_hydro.plot(label='SFOE Constraint')


# Plot series

# Hydro

hydro = pd.read_csv(
    'output/benchmarked_hourly_hydro.csv',
    parse_dates=['DateTime'],
)
# Following fails due to a column that contains string values 
# which is fed to Polars'
#   .with_columns(pl.exclude(time_column).cast(pl.Float64))
# trying to convert that string column into a float, which is impossible
# ----------------------------------------------------------------------------
# hydro = read_csv(
#     # source=entsoe_csv_file,
#     source='output/benchmarked_hourly_hydro.csv',
#     start=START,
#     end=END,
#     time_column='DateTime',
# )
# ----------------------------------------------------------------------------
hydro = hydro.set_index('DateTime')
hydro_target = sfoe_daily['Flusskraft'] + sfoe_daily['Speicherkraft']

# --- Daily comparison: hydro ---
hydro_bench_daily = hydro['hydro_benchmarked_gwh'].resample('D').sum()

# --- Hourly before/after comparison: hydro ---
plot_series_before_and_after(
    dataframe=hydro,
    original_series='hydro_entsoe_original_gwh',
    adjusted_series='hydro_benchmarked_gwh',
    data_source='ENTSO-E',
    electricity_generation_type='Hydro',
    frequency='hourly',
)

# --- Daily difference plot: hydro ---
plot_series_difference(
    target_series=hydro_target,
    benchmarked_series=hydro_bench_daily,
    data_source='SFOE',
    electricity_generation_type='Hydro',
    frequency='daily',
    # target_series_label: str = "Target series",
    # benchmarked_series_label: str = "Benchmarked series",
    # units: str = "GWh",
    # xlabel: str = "Time",
    # output_directory: Path = Path("output"),
)

# Nuclear

nuclear = pd.read_csv('output/benchmarked_hourly_nuclear.csv', parse_dates=['DateTime'])
nuclear = nuclear.set_index('DateTime')
nuclear_target = sfoe_daily['Kernkraft']

# --- Hourly before/after comparison: nuclear ---
plot_series_before_and_after(
    dataframe=nuclear,
    original_series='nuclear_entsoe_original_gwh',
    adjusted_series='nuclear_benchmarked_gwh',
    data_source='ENTSO-E',
    electricity_generation_type='Nuclear',
    frequency='hourly',
)

# --- Daily difference plot: nuclear ---
nuclear_bench_daily = nuclear['nuclear_benchmarked_gwh'].resample('D').sum()

plot_series_difference(
    target_series=nuclear_target,
    benchmarked_series=nuclear_bench_daily,
    data_source='SFOE',
    electricity_generation_type='Nuclear',
    frequency='daily',
    # label='SFOE daily target',
)
