# ENTSO-E Transparency Platform API Skill

## Overview
This skill enables Claude Code to collect electricity data from the ENTSO-E (European Network of Transmission System Operators for Electricity) Transparency Platform, focusing on France's electricity market data.

## What is ENTSO-E?
ENTSO-E Transparency Platform provides open-access electricity generation, transportation, and consumption data for the pan-European market. Data includes:
- Load (consumption) and forecasts
- Generation by type (solar, wind, nuclear, etc.)
- Day-ahead and actual prices
- Cross-border flows
- Transmission capacity
- Balancing and outages

## Prerequisites

### 1. API Token Required
Before using the API, you MUST obtain an API token:

1. Register at https://transparency.entsoe.eu/
2. Send an email to `transparency@entsoe.eu` with:
   - Subject: "Restful API access"
   - Body: Your registered email address
3. Wait 3 working days for approval
4. Find your token under "Web API Security Token" in your account settings

### 2. Install the Python Client

```bash
pip install entsoe-py --break-system-packages
```

## Using the API

### Basic Setup

The `entsoe-py` library provides two client types:

1. **EntsoePandasClient**: Returns data as pandas DataFrame/Series (RECOMMENDED)
2. **EntsoeRawClient**: Returns raw XML data

### Quick Start Example for France

```python
from entsoe import EntsoePandasClient
import pandas as pd

# Initialize client with your API token
API_TOKEN = "your-token-here"
client = EntsoePandasClient(api_key=API_TOKEN)

# Define time range (must include timezone)
start = pd.Timestamp('20240201', tz='Europe/Paris')
end = pd.Timestamp('20240229T2359', tz='Europe/Paris')

# France country code
country_code = 'FR'

# Query electricity load (consumption)
load_data = client.query_load(country_code, start=start, end=end)

# Query day-ahead prices
prices = client.query_day_ahead_prices(country_code, start=start, end=end)

# Query generation by type
generation = client.query_generation(country_code, start=start, end=end)
```

## Common Data Queries for France

### 1. Electricity Consumption (Load)

```python
# Actual load
load = client.query_load('FR', start=start, end=end)

# Load forecast
load_forecast = client.query_load_forecast('FR', start=start, end=end)
```

### 2. Electricity Prices

```python
# Day-ahead prices (€/MWh)
day_ahead_prices = client.query_day_ahead_prices('FR', start=start, end=end)
```

### 3. Generation by Energy Source

```python
# All generation types (nuclear, solar, wind, hydro, etc.)
generation = client.query_generation('FR', start=start, end=end)

# Returns DataFrame with columns for each generation type:
# - Nuclear
# - Solar
# - Wind Onshore
# - Wind Offshore
# - Hydro Run-of-river and poundage
# - Hydro Water Reservoir
# - Hydro Pumped Storage
# - Fossil Gas
# - Fossil Hard coal
# - Fossil Oil
# - Biomass
# - Other renewable
```

### 4. Wind and Solar Forecasts

```python
# Wind and solar generation forecast
wind_solar_forecast = client.query_wind_and_solar_forecast(
    'FR', start=start, end=end
)

# Specific type (Wind Onshore, Wind Offshore, Solar)
solar_forecast = client.query_wind_and_solar_forecast(
    'FR', start=start, end=end, psr_type='B16'  # B16 = Solar
)
```

### 5. Cross-Border Flows

```python
# Physical flows between France and neighboring countries
flows_fr_de = client.query_crossborder_flows(
    'FR', 'DE_LU', start=start, end=end
)

# Scheduled exchanges
scheduled_fr_es = client.query_scheduled_exchanges(
    'FR', 'ES', start=start, end=end
)
```

### 6. Installed Generation Capacity

```python
# Installed capacity by production type
installed_capacity = client.query_installed_generation_capacity(
    'FR', start=start, end=end
)
```

## Country and Area Codes

France uses the code **`FR`** for most queries.

Other European countries:
- Belgium: `BE`
- Germany-Luxembourg: `DE_LU`
- Spain: `ES`
- Italy: `IT_SACO_AC`
- Netherlands: `NL`
- Switzerland: `CH`
- United Kingdom: `GB`

Full list available in the entsoe-py library's mappings.

## PSR Type Codes (Production Source Types)

When querying specific generation types, use these codes:

- `B01`: Biomass
- `B02`: Fossil Brown coal/Lignite
- `B03`: Fossil Coal-derived gas
- `B04`: Fossil Gas
- `B05`: Fossil Hard coal
- `B06`: Fossil Oil
- `B09`: Geothermal
- `B10`: Hydro Pumped Storage
- `B11`: Hydro Run-of-river and poundage
- `B12`: Hydro Water Reservoir
- `B13`: Marine
- `B14`: Nuclear
- `B15`: Other renewable
- `B16`: Solar
- `B18`: Wind Offshore
- `B19`: Wind Onshore

## Best Practices

### 1. Timezone Management
**ALWAYS specify timezone** when creating timestamps. For France, use `'Europe/Paris'`:

```python
start = pd.Timestamp('20240101', tz='Europe/Paris')  # GOOD
start = pd.Timestamp('20240101')  # BAD - will cause errors
```

### 2. Date Range Limitations
- API has limits on query range length (typically 1 year max)
- For longer periods, split into smaller chunks

```python
def query_long_period(client, country_code, start, end, query_func):
    """Split long queries into yearly chunks"""
    results = []
    current = start
    
    while current < end:
        chunk_end = min(current + pd.DateOffset(years=1), end)
        data = query_func(country_code, start=current, end=chunk_end)
        results.append(data)
        current = chunk_end
    
    return pd.concat(results)
```

### 3. Rate Limiting
- Maximum 100 requests per minute per user
- Exceeding limit results in 10-minute ban
- Add delays between requests if making many calls

```python
import time

for country in countries:
    data = client.query_load(country, start, end)
    time.sleep(0.6)  # Stay under 100 req/min
```

### 4. Error Handling
The API may return "No matching data" errors for valid requests when data is unavailable:

```python
from entsoe.exceptions import NoMatchingDataError

try:
    data = client.query_generation('FR', start=start, end=end)
except NoMatchingDataError:
    print("No data available for this period")
except Exception as e:
    print(f"API error: {e}")
```

### 5. Data Quality Checks
- Check for missing values: `df.isna().sum()`
- Verify timestamp continuity
- Report data issues to: transparency@entsoe.eu

## Data Processing Tips

### Resampling and Aggregation

```python
# Resample to hourly averages
hourly = generation.resample('1H').mean()

# Daily totals
daily = generation.resample('1D').sum()

# Group by hour of day
generation['hour'] = generation.index.hour
hourly_pattern = generation.groupby('hour').mean()
```

### Exporting Data

```python
# Save to CSV
generation.to_csv('france_generation.csv')

# Save to Excel
with pd.ExcelWriter('france_electricity_data.xlsx') as writer:
    generation.to_excel(writer, sheet_name='Generation')
    prices.to_excel(writer, sheet_name='Prices')
    load.to_excel(writer, sheet_name='Load')
```

### Visualization

```python
import matplotlib.pyplot as plt

# Plot generation mix
generation.plot(kind='area', stacked=True, figsize=(12, 6))
plt.title('France Electricity Generation by Source')
plt.ylabel('MW')
plt.xlabel('Date')
plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
plt.tight_layout()
plt.savefig('france_generation_mix.png', dpi=300)
```

## Common Pitfalls

1. **Forgetting timezone**: All timestamps MUST have timezone info
2. **Wrong country code**: Use 'FR' not 'FRA' or 'France'
3. **Date range too long**: Split queries into smaller chunks
4. **Not handling missing data**: Some periods may have no data
5. **Hardcoded API token**: Use environment variables instead

```python
import os
API_TOKEN = os.getenv('ENTSOE_API_TOKEN')
```

## Advanced: Direct REST API Usage

If you need more control or encounter issues with entsoe-py:

```python
import requests

API_ENDPOINT = 'https://web-api.tp.entsoe.eu/api'
API_TOKEN = 'your-token-here'

params = {
    'securityToken': API_TOKEN,
    'documentType': 'A75',  # Actual generation per type
    'processType': 'A16',   # Realised
    'in_Domain': '10YFR-RTE------C',  # France EIC code
    'periodStart': '202401010000',  # Format: YYYYMMDDHHmm
    'periodEnd': '202401312359'
}

response = requests.get(API_ENDPOINT, params=params)
xml_data = response.text
```

Document types and parameters: https://documenter.getpostman.com/view/7009892/2s93JtP3F6

## Resources

- **Official API Documentation**: https://documenter.getpostman.com/view/7009892/2s93JtP3F6
- **Help Center**: https://transparencyplatform.zendesk.com/hc/en-us
- **entsoe-py GitHub**: https://github.com/EnergieID/entsoe-py
- **ENTSO-E Platform**: https://transparency.entsoe.eu/

## Support

For API issues, contact: transparency@entsoe.eu

## Example: Complete France Electricity Analysis

```python
from entsoe import EntsoePandasClient
import pandas as pd
import matplotlib.pyplot as plt

# Setup
API_TOKEN = "your-token-here"
client = EntsoePandasClient(api_key=API_TOKEN)

# Time range
start = pd.Timestamp('20240101', tz='Europe/Paris')
end = pd.Timestamp('20240131T2359', tz='Europe/Paris')

# Collect all data
print("Fetching load data...")
load = client.query_load('FR', start=start, end=end)

print("Fetching generation data...")
generation = client.query_generation('FR', start=start, end=end)

print("Fetching price data...")
prices = client.query_day_ahead_prices('FR', start=start, end=end)

# Analysis
print(f"\nAverage load: {load.mean():.2f} MW")
print(f"Peak load: {load.max():.2f} MW")
print(f"Average price: {prices.mean():.2f} €/MWh")

# Identify peak nuclear generation
if 'Nuclear' in generation.columns:
    nuclear_capacity = generation['Nuclear'].max()
    print(f"Peak nuclear generation: {nuclear_capacity:.2f} MW")

# Export
generation.to_csv('france_generation_jan2024.csv')
prices.to_csv('france_prices_jan2024.csv')

print("\nData collection complete!")
```

## Notes

- This skill focuses on France but works for all European countries
- Data availability varies by country and data type
- Historical data typically available from January 2015 onwards
- Some data types are updated with delay (check documentation for specifics)
