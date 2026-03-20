# Python Programming Skill

## Overview
This skill provides best practices and guidelines for writing high-quality Python code in Claude Code, covering project structure, coding standards, common patterns, and tooling.

## Python Version
- **Target version**: Python 3.9+ (Ubuntu 24 default is Python 3.12)
- Check version: `python3 --version`
- Use `python3` command explicitly (not `python`)

## Project Structure

### Standard Python Project Layout

```
project/
├── README.md
├── requirements.txt          # pip dependencies
├── setup.py or pyproject.toml  # package configuration
├── .gitignore
├── src/                      # source code (recommended)
│   └── myproject/
│       ├── __init__.py
│       ├── main.py
│       ├── utils.py
│       └── config.py
├── tests/                    # test files
│   ├── __init__.py
│   ├── test_main.py
│   └── test_utils.py
├── docs/                     # documentation
├── data/                     # data files
│   ├── raw/
│   └── processed/
├── notebooks/                # Jupyter notebooks
└── scripts/                  # utility scripts
```

### Simple Project Structure

For smaller projects:

```
project/
├── README.md
├── requirements.txt
├── main.py
├── utils.py
├── config.py
└── data/
```

## Package Management

### Using uv (Recommended)

`uv` is a fast Python package installer and resolver written in Rust. It's significantly faster than pip and handles dependencies better.

#### Installing uv

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv --break-system-packages
```

#### Basic uv Commands

```bash
# Install package
uv pip install package_name

# Install specific version
uv pip install package_name==1.2.3

# Install from requirements.txt
uv pip install -r requirements.txt

# Install multiple packages
uv pip install pandas numpy matplotlib

# Uninstall package
uv pip uninstall package_name

# List installed packages
uv pip list

# Show package info
uv pip show package_name

# Generate requirements.txt from current environment
uv pip freeze > requirements.txt
```

**Note**: uv doesn't require the `--break-system-packages` flag that pip needs in Claude Code.

### Project Setup with uv

#### Option 1: Using pyproject.toml (Modern, Recommended)

Create a `pyproject.toml` file:

```toml
[project]
name = "myproject"
version = "0.1.0"
description = "My electricity data analysis project"
requires-python = ">=3.9"
dependencies = [
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "matplotlib>=3.7.0",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
    "entsoe-py>=0.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

Then install:

```bash
# Install main dependencies
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"
```

#### Option 2: Using requirements.txt (Traditional)

```txt
# requirements.txt
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
requests>=2.31.0
python-dotenv>=1.0.0
entsoe-py>=0.5.0
```

Install:

```bash
uv pip install -r requirements.txt
```

Use `>=` for flexibility, `==` for exact versions when needed for reproducibility.

### Using Virtual Environments with uv

uv makes virtual environment management easier:

```bash
# Create virtual environment with uv (faster than python -m venv)
uv venv

# Create with specific Python version
uv venv --python 3.11

# Activate (Linux/Mac)
source .venv/bin/activate

# Install packages in virtual environment
uv pip install -r requirements.txt

# Deactivate
deactivate
```

### uv vs pip Comparison

| Feature | uv | pip |
|---------|-----|-----|
| Speed | 10-100x faster | Baseline |
| Dependency resolution | Better conflict resolution | Basic |
| Virtual env creation | Built-in & fast | Separate tool (venv) |
| Caching | Advanced caching | Basic |
| Lock files | Supported | Requires pip-tools |

### Advanced uv Features

```bash
# Compile requirements.txt to requirements.lock with exact versions
uv pip compile requirements.txt -o requirements.lock

# Sync environment to exact requirements
uv pip sync requirements.lock

# Update all packages to latest compatible versions
uv pip install --upgrade -r requirements.txt

# Install package in editable mode (for development)
uv pip install -e .

# Show dependency tree
uv pip tree
```

## Code Style and Standards

### Follow PEP 8

PEP 8 is Python's official style guide. Key points:

**Indentation**: 4 spaces (never tabs)

```python
# Good
def my_function():
    if condition:
        do_something()
        
# Bad
def my_function():
  if condition:
    do_something()
```

**Line Length**: Max 79 characters (88 for Black formatter)

```python
# Good
result = some_function(
    argument1,
    argument2,
    argument3
)

# Bad
result = some_function(argument1, argument2, argument3, argument4, argument5, argument6)
```

**Naming Conventions**:
- Variables/functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_CASE`
- Private: `_leading_underscore`

```python
# Good naming
class DataProcessor:
    MAX_RETRIES = 3
    
    def __init__(self):
        self.data_count = 0
        self._internal_cache = {}
    
    def process_data(self, input_file):
        pass
```

**Imports**: Grouped and ordered

```python
# Standard library
import os
import sys
from datetime import datetime

# Third-party
import pandas as pd
import numpy as np
import requests

# Local application
from myproject import utils
from myproject.config import settings
```

### Type Hints (Python 3.5+)

Use type hints for better code clarity and IDE support:

```python
from typing import List, Dict, Optional, Union, Tuple

def process_data(
    data: List[float],
    threshold: float = 0.5,
    options: Optional[Dict[str, str]] = None
) -> Tuple[List[float], int]:
    """Process numerical data above threshold.
    
    Args:
        data: List of numerical values
        threshold: Minimum value to include
        options: Optional configuration dictionary
        
    Returns:
        Tuple of (filtered data, count of filtered items)
    """
    if options is None:
        options = {}
    
    filtered = [x for x in data if x > threshold]
    return filtered, len(filtered)
```

### Docstrings

Use Google or NumPy style docstrings:

```python
def calculate_statistics(data, include_median=True):
    """Calculate statistical measures for a dataset.
    
    Args:
        data (list or np.array): Input data values
        include_median (bool): Whether to include median in results
        
    Returns:
        dict: Dictionary containing statistical measures:
            - 'mean': arithmetic mean
            - 'std': standard deviation
            - 'median': median value (if include_median=True)
            
    Raises:
        ValueError: If data is empty
        TypeError: If data is not numeric
        
    Example:
        >>> data = [1, 2, 3, 4, 5]
        >>> stats = calculate_statistics(data)
        >>> print(stats['mean'])
        3.0
    """
    if not data:
        raise ValueError("Data cannot be empty")
    
    import numpy as np
    arr = np.array(data)
    
    results = {
        'mean': arr.mean(),
        'std': arr.std()
    }
    
    if include_median:
        results['median'] = np.median(arr)
    
    return results
```

## Common Patterns and Best Practices

### 1. File I/O

```python
# Use context managers (with statement)
# Good - file automatically closed
with open('data.txt', 'r') as f:
    content = f.read()

# Bad - must remember to close
f = open('data.txt', 'r')
content = f.read()
f.close()

# Read lines
with open('data.txt', 'r') as f:
    lines = f.readlines()
    
# Write file
with open('output.txt', 'w') as f:
    f.write('Hello, World!\n')

# JSON files
import json

with open('config.json', 'r') as f:
    config = json.load(f)

with open('output.json', 'w') as f:
    json.dump(data, f, indent=2)
```

### 2. Path Handling

Use `pathlib` instead of string concatenation:

```python
from pathlib import Path

# Good - cross-platform
data_dir = Path('data')
input_file = data_dir / 'input.csv'
output_file = data_dir / 'processed' / 'output.csv'

# Create directory if doesn't exist
output_file.parent.mkdir(parents=True, exist_ok=True)

# Check if exists
if input_file.exists():
    print(f"Found file: {input_file}")

# Iterate over files
for file in data_dir.glob('*.csv'):
    print(file.name)

# Bad - platform-dependent
import os
input_file = os.path.join('data', 'input.csv')
```

### 3. Configuration Management

```python
# config.py
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration."""
    
    # Paths
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / 'data'
    OUTPUT_DIR = BASE_DIR / 'output'
    
    # API credentials
    API_KEY = os.getenv('API_KEY')
    API_URL = os.getenv('API_URL', 'https://api.default.com')
    
    # Processing parameters
    BATCH_SIZE = 100
    MAX_RETRIES = 3
    TIMEOUT = 30

# Usage in other files
from config import Config

api_key = Config.API_KEY
data_path = Config.DATA_DIR / 'input.csv'
```

### 4. Error Handling

```python
# Specific exceptions
try:
    with open('data.csv', 'r') as f:
        data = f.read()
except FileNotFoundError:
    print("File not found. Using default data.")
    data = get_default_data()
except PermissionError:
    print("Permission denied to read file.")
    raise
except Exception as e:
    print(f"Unexpected error: {e}")
    raise

# Custom exceptions
class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass

def validate_data(data):
    if not data:
        raise DataValidationError("Data cannot be empty")
    if len(data) < 10:
        raise DataValidationError("Data must have at least 10 entries")
```

### 5. Logging

Use logging instead of print statements:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger(__name__)

# Use in code
logger.info("Starting data processing")
logger.warning("Missing values detected")
logger.error("Failed to connect to API")
logger.debug("Variable value: %s", variable)

# For specific modules
# data_processor.py
logger = logging.getLogger('myapp.data_processor')
```

### 6. List Comprehensions

```python
# Good - concise and Pythonic
squares = [x**2 for x in range(10)]
even_squares = [x**2 for x in range(10) if x % 2 == 0]

# Dictionary comprehension
word_lengths = {word: len(word) for word in words}

# Set comprehension
unique_lengths = {len(word) for word in words}

# Generator expression (memory efficient)
sum_squares = sum(x**2 for x in range(1000000))

# Bad - verbose
squares = []
for x in range(10):
    squares.append(x**2)
```

### 7. String Formatting

```python
name = "Alice"
age = 30
value = 3.14159

# f-strings (Python 3.6+, preferred)
message = f"Hello, {name}! You are {age} years old."
formatted = f"Value: {value:.2f}"

# str.format() (older style)
message = "Hello, {}! You are {} years old.".format(name, age)

# Old % formatting (avoid)
message = "Hello, %s! You are %d years old." % (name, age)
```

### 8. Working with Dates

```python
from datetime import datetime, timedelta
import pandas as pd

# Current time
now = datetime.now()
today = datetime.today()

# Parsing
date_str = "2024-01-15"
date = datetime.strptime(date_str, "%Y-%m-%d")

# Formatting
formatted = date.strftime("%B %d, %Y")  # "January 15, 2024"

# Arithmetic
tomorrow = now + timedelta(days=1)
last_week = now - timedelta(weeks=1)

# Pandas timestamps (better for data analysis)
ts = pd.Timestamp('2024-01-15')
date_range = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')

# Timezone-aware (important for ENTSO-E API!)
import pytz
paris_tz = pytz.timezone('Europe/Paris')
date_with_tz = datetime(2024, 1, 15, tzinfo=paris_tz)

# Pandas with timezone
ts_paris = pd.Timestamp('2024-01-15', tz='Europe/Paris')
```

## Data Science Libraries

### NumPy

```python
import numpy as np

# Create arrays
arr = np.array([1, 2, 3, 4, 5])
zeros = np.zeros((3, 4))
ones = np.ones((2, 3))
random_arr = np.random.rand(3, 3)

# Array operations
arr_squared = arr ** 2
arr_sum = arr.sum()
arr_mean = arr.mean()
arr_std = arr.std()

# Boolean indexing
filtered = arr[arr > 2]

# Reshaping
reshaped = arr.reshape(5, 1)
```

### Pandas

```python
import pandas as pd

# Read data
df = pd.read_csv('data.csv')
df = pd.read_excel('data.xlsx', sheet_name='Sheet1')
df = pd.read_json('data.json')

# Basic info
print(df.head())
print(df.info())
print(df.describe())

# Column operations
df['new_col'] = df['col1'] + df['col2']
df['category'] = df['value'].apply(lambda x: 'high' if x > 10 else 'low')

# Filtering
filtered = df[df['age'] > 30]
filtered = df[(df['age'] > 30) & (df['city'] == 'Paris')]

# Grouping
grouped = df.groupby('category')['value'].mean()
agg_df = df.groupby('category').agg({
    'value': ['mean', 'sum', 'count'],
    'age': 'max'
})

# Time series
df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')
monthly = df.resample('M').mean()

# Handling missing data
df_clean = df.dropna()
df_filled = df.fillna(0)
df_filled = df.fillna(method='ffill')

# Merge/join
merged = pd.merge(df1, df2, on='id', how='left')

# Export
df.to_csv('output.csv', index=False)
df.to_excel('output.xlsx', index=False)
```

### Matplotlib

```python
import matplotlib.pyplot as plt
import numpy as np

# Basic plot
x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(10, 6))
plt.plot(x, y, label='sin(x)')
plt.xlabel('x')
plt.ylabel('y')
plt.title('Sine Wave')
plt.legend()
plt.grid(True)
plt.savefig('plot.png', dpi=300, bbox_inches='tight')
plt.close()

# Multiple subplots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

axes[0, 0].plot(x, y)
axes[0, 0].set_title('Plot 1')

axes[0, 1].scatter(x, y)
axes[0, 1].set_title('Plot 2')

axes[1, 0].hist(y, bins=20)
axes[1, 0].set_title('Plot 3')

axes[1, 1].bar(['A', 'B', 'C'], [1, 2, 3])
axes[1, 1].set_title('Plot 4')

plt.tight_layout()
plt.savefig('subplots.png')
plt.close()

# Pandas integration
df.plot(kind='line', x='date', y='value', figsize=(12, 6))
plt.savefig('timeseries.png')
plt.close()
```

## API Requests

### Using requests library

```python
import requests
from typing import Dict, Any

def fetch_data(url: str, params: Dict[str, Any] = None) -> Dict:
    """Fetch data from API with error handling."""
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()  # Raise exception for bad status codes
        return response.json()
    except requests.exceptions.Timeout:
        print("Request timed out")
        raise
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise

# POST request
def post_data(url: str, data: Dict[str, Any]) -> Dict:
    """Send POST request with JSON data."""
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=data, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

# With authentication
def fetch_with_auth(url: str, api_key: str) -> Dict:
    """Fetch data with API key authentication."""
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()

# Session for multiple requests
session = requests.Session()
session.headers.update({'Authorization': f'Bearer {api_key}'})

response1 = session.get(url1)
response2 = session.get(url2)
```

## Testing

### Using pytest

```python
# test_calculations.py
import pytest
from myproject import calculations

def test_add():
    """Test addition function."""
    assert calculations.add(2, 3) == 5
    assert calculations.add(-1, 1) == 0

def test_divide():
    """Test division function."""
    assert calculations.divide(10, 2) == 5
    assert calculations.divide(5, 2) == 2.5

def test_divide_by_zero():
    """Test that dividing by zero raises exception."""
    with pytest.raises(ZeroDivisionError):
        calculations.divide(10, 0)

@pytest.fixture
def sample_data():
    """Fixture providing sample data for tests."""
    return [1, 2, 3, 4, 5]

def test_mean(sample_data):
    """Test mean calculation with fixture."""
    assert calculations.mean(sample_data) == 3.0

# Run tests: pytest test_calculations.py
```

## Performance Optimization

### Timing Code

```python
import time
from functools import wraps

# Simple timing
start = time.time()
# ... code to time ...
end = time.time()
print(f"Execution time: {end - start:.2f} seconds")

# Decorator for timing functions
def timer(func):
    """Decorator to time function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(2)
    return "Done"

# Using timeit for benchmarking
import timeit

time_taken = timeit.timeit(
    'sum(range(1000))',
    number=10000
)
print(f"Time: {time_taken:.4f} seconds")
```

### Memory Efficiency

```python
# Use generators for large datasets
def read_large_file(filepath):
    """Generator to read file line by line."""
    with open(filepath, 'r') as f:
        for line in f:
            yield line.strip()

# Bad - loads entire file into memory
with open('huge_file.txt', 'r') as f:
    lines = f.readlines()  # Could cause memory issues

# Good - processes line by line
for line in read_large_file('huge_file.txt'):
    process(line)

# Generator expressions vs list comprehensions
# Memory efficient
sum_squares = sum(x**2 for x in range(1000000))

# Memory intensive
sum_squares = sum([x**2 for x in range(1000000)])
```

## Common Pitfalls

### 1. Mutable Default Arguments

```python
# Bad - mutable default is shared across calls
def add_item(item, items=[]):
    items.append(item)
    return items

# Good - use None and create new list
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

### 2. Late Binding in Closures

```python
# Bad - all functions refer to same 'i'
funcs = [lambda: i for i in range(5)]
[f() for f in funcs]  # [4, 4, 4, 4, 4]

# Good - capture current value
funcs = [lambda i=i: i for i in range(5)]
[f() for f in funcs]  # [0, 1, 2, 3, 4]
```

### 3. Copying Objects

```python
import copy

# Shallow copy
original = [[1, 2], [3, 4]]
shallow = original.copy()
shallow[0][0] = 99  # Affects original!

# Deep copy
deep = copy.deepcopy(original)
deep[0][0] = 99  # Doesn't affect original
```

## Environment Variables

```python
import os
from dotenv import load_dotenv

# .env file:
# API_KEY=your_secret_key
# DATABASE_URL=postgresql://localhost/mydb
# DEBUG=True

# Load .env file
load_dotenv()

# Access variables
api_key = os.getenv('API_KEY')
db_url = os.getenv('DATABASE_URL')
debug = os.getenv('DEBUG', 'False') == 'True'

# Never hardcode secrets
# Bad
API_KEY = "sk_live_abc123xyz"

# Good
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY environment variable not set")
```

## Command Line Arguments

```python
import argparse

def main():
    parser = argparse.ArgumentParser(
        description='Process electricity data'
    )
    
    parser.add_argument(
        'input_file',
        help='Path to input CSV file'
    )
    
    parser.add_argument(
        '--output',
        '-o',
        default='output.csv',
        help='Output file path (default: output.csv)'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        required=True,
        help='Start date (YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    
    print(f"Processing {args.input_file}")
    if args.verbose:
        print(f"Output will be saved to {args.output}")
    
    # Use arguments
    process_data(args.input_file, args.output, args.start_date)

if __name__ == '__main__':
    main()

# Run: python script.py data.csv --start-date 2024-01-01 -v
```

## Script Template

```python
#!/usr/bin/env python3
"""
Script description here.

Installation:
    uv pip install -r requirements.txt

Usage:
    python script.py input.csv --output results.csv
"""

import logging
from pathlib import Path
from typing import List, Dict
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def process_data(input_path: Path, output_path: Path) -> None:
    """Process data from input file and save results.
    
    Args:
        input_path: Path to input file
        output_path: Path to output file
    """
    logger.info(f"Processing {input_path}")
    
    try:
        # Your processing logic here
        pass
    except Exception as e:
        logger.error(f"Failed to process data: {e}")
        raise
    
    logger.info(f"Results saved to {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_file', type=Path, help='Input file path')
    parser.add_argument('--output', '-o', type=Path, default=Path('output.csv'),
                        help='Output file path')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate inputs
    if not args.input_file.exists():
        logger.error(f"Input file not found: {args.input_file}")
        return 1
    
    # Create output directory if needed
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        process_data(args.input_file, args.output)
        return 0
    except Exception as e:
        logger.exception("Script failed")
        return 1


if __name__ == '__main__':
    exit(main())
```

## Useful Built-in Functions

```python
# enumerate - get index and value
for idx, value in enumerate(['a', 'b', 'c']):
    print(f"{idx}: {value}")

# zip - iterate over multiple lists
names = ['Alice', 'Bob', 'Charlie']
ages = [25, 30, 35]
for name, age in zip(names, ages):
    print(f"{name} is {age} years old")

# sorted - sort with key function
words = ['banana', 'pie', 'Washington', 'book']
sorted_by_length = sorted(words, key=len)
sorted_lower = sorted(words, key=str.lower)

# filter - filter items
numbers = [1, 2, 3, 4, 5, 6]
evens = list(filter(lambda x: x % 2 == 0, numbers))

# map - apply function to all items
squared = list(map(lambda x: x**2, numbers))

# any, all - check conditions
has_even = any(x % 2 == 0 for x in numbers)
all_positive = all(x > 0 for x in numbers)
```

## Resources

- **Official Python Docs**: https://docs.python.org/3/
- **PEP 8 Style Guide**: https://pep8.org/
- **Real Python Tutorials**: https://realpython.com/
- **Python Package Index (PyPI)**: https://pypi.org/
- **uv Documentation**: https://github.com/astral-sh/uv

## Complete Project Workflow with uv

Here's a typical workflow for starting a new project:

```bash
# 1. Create project directory
mkdir my-electricity-project
cd my-electricity-project

# 2. Create virtual environment with uv
uv venv

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Create pyproject.toml or requirements.txt
cat > requirements.txt << EOF
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
entsoe-py>=0.5.0
python-dotenv>=1.0.0
EOF

# 5. Install dependencies
uv pip install -r requirements.txt

# 6. Create project structure
mkdir -p src/myproject data/{raw,processed} tests

# 7. Start coding!
touch src/myproject/__init__.py
touch src/myproject/main.py
```

For reproducible environments:

```bash
# Lock exact versions
uv pip compile requirements.txt -o requirements.lock

# Install exact versions on another machine
uv pip sync requirements.lock
```

## Quick Reference

### Common uv commands
```bash
uv pip install <package>        # Install package
uv pip install -r requirements.txt  # Install from file
uv pip uninstall <package>      # Remove package
uv pip list                     # List installed
uv pip freeze                   # Export installed packages
uv pip compile requirements.txt # Create lock file
uv pip sync requirements.lock   # Install exact versions
uv venv                         # Create virtual environment
```

### Common packages
- **Data**: pandas, numpy, scipy
- **Visualization**: matplotlib, seaborn, plotly
- **API**: requests, httpx
- **Web**: flask, fastapi
- **Testing**: pytest, unittest
- **Utilities**: python-dotenv, click, tqdm
- **Dates**: python-dateutil, pytz

### Debugging
```python
# Print debugging
print(f"Debug: {variable}")

# Interactive debugger
import pdb; pdb.set_trace()

# Better debugging with ipdb
import ipdb; ipdb.set_trace()

# Assertions for development
assert len(data) > 0, "Data cannot be empty"
```

This skill covers Python fundamentals through advanced patterns for professional development in Claude Code.
