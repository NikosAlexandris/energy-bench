import pandas as pd

# 1) Read benchmarked hourly hydro
h = pd.read_csv(
        'output/benchmarked_hourly_hydro.csv',
        parse_dates=['DateTime'],
        index_col='DateTime',
)
h['hydro_benchmarked_gwh'] = pd.to_numeric(h['hydro_benchmarked_gwh'], errors='coerce')
h = h.dropna(subset=['hydro_benchmarked_gwh'])

# 2) Sum hourly values back to daily
h_daily = h['hydro_benchmarked_gwh'].resample('D').sum()
print(f'{h_daily=}')

# 3) Build SFOE daily reference
sfoe = pd.read_csv(
    'data/SFOE/swissgrid_daily_production_2015_2026.csv',
    parse_dates=['Date'],
    index_col='Date',
)
# sfoe = sfoe.set_index('Date')
sfoe_daily = sfoe['Flusskraft'] + sfoe['Speicherkraft']
print(f'{sfoe_daily=}')

# 4) Compare
check = pd.DataFrame({
    'benchmarked_daily_sum': h_daily,
    'sfoe_daily_total': sfoe_daily
})
check['difference'] = check['benchmarked_daily_sum'] - check['sfoe_daily_total']

print()
print(check.round(6))
print('\nMax absolute difference:', check['difference'].abs().max())
