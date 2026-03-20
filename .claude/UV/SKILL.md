# uv Package Manager Skill

## Overview
`uv` is an extremely fast Python package and project manager written in Rust by Astral (creators of Ruff). It serves as a unified replacement for pip, pip-tools, pipx, virtualenv, pyenv, poetry, and more—providing 10-100x faster performance than traditional tools.

## Why Use uv?

### Speed
- **10-100x faster** than pip for package installation
- **80x faster** than `python -m venv` for virtual environment creation
- **115x faster** with warm cache
- Written in Rust for maximum performance

### Simplicity
- **Drop-in replacement** for pip, pip-tools, and virtualenv
- **No Python required** to install uv
- **Single binary** with no dependencies
- **Compatible** with existing requirements.txt workflows

### Features
- Unified tool for packages, environments, Python versions, and tools
- Universal lock files for reproducible builds
- Automatic Python version installation and management
- Built-in workspace support for monorepos
- Global cache for disk space efficiency
- Cross-platform: Linux, macOS, Windows

## Installation

### Quick Install (Recommended)

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Using pip (if you have Python already)
pip install uv
```

### Verify Installation

```bash
uv --version
```

### Update uv

```bash
# Self-update to latest version
uv self update

# If installed via pip
pip install --upgrade uv
```

## Core Commands

### 1. Package Installation (pip Interface)

uv provides a drop-in replacement for pip commands:

```bash
# Install a package
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

# Show package information
uv pip show package_name

# Export installed packages
uv pip freeze > requirements.txt
```

**No `--break-system-packages` flag needed!**

### 2. Virtual Environments

```bash
# Create virtual environment (80x faster than venv)
uv venv

# Create with specific Python version
uv venv --python 3.11

# Create with custom name/path
uv venv myenv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Deactivate
deactivate
```

### 3. Python Version Management

uv can install and manage Python versions automatically:

```bash
# Install specific Python version
uv python install 3.12

# Install multiple versions
uv python install 3.11 3.12 3.13

# List installed Python versions
uv python list

# List available Python versions
uv python list --all-versions

# Find Python installations
uv python find

# Pin Python version for project
uv python pin 3.12

# Uninstall Python version
uv python uninstall 3.11
```

### 4. Dependency Compilation and Syncing

Advanced dependency management with lock files:

```bash
# Compile requirements.in to requirements.txt with resolved versions
uv pip compile requirements.in -o requirements.txt

# Compile with platform-independent resolution
uv pip compile requirements.in --universal -o requirements.txt

# Sync environment to exact requirements (removes extras)
uv pip sync requirements.txt

# Install from compiled lock file
uv pip install -r requirements.txt
```

### 5. Project Management

Modern project workflow with pyproject.toml:

```bash
# Initialize a new project
uv init myproject
cd myproject

# Add a dependency (auto-creates venv if needed)
uv add pandas

# Add multiple dependencies
uv add numpy matplotlib requests

# Add development dependency
uv add --dev pytest black ruff

# Remove dependency
uv remove package_name

# Update dependencies
uv lock --upgrade

# Install all project dependencies
uv sync

# Run command in project environment
uv run python script.py
uv run pytest
```

### 6. Tool Management (replaces pipx)

Install and run command-line tools without polluting project environments:

```bash
# Run tool without installing (ephemeral)
uvx ruff check .
uvx black .
uvx pytest

# Install tool globally
uv tool install ruff
uv tool install black
uv tool install pytest

# List installed tools
uv tool list

# Update tool
uv tool upgrade ruff

# Uninstall tool
uv tool uninstall ruff

# Run specific version
uvx ruff@0.1.0 check .
```

### 7. Script Dependencies

Run single-file scripts with inline dependencies:

```python
# script.py
# /// script
# dependencies = [
#   "requests",
#   "pandas>=2.0",
# ]
# ///

import requests
import pandas as pd

response = requests.get("https://api.example.com/data")
df = pd.DataFrame(response.json())
print(df.head())
```

Run the script:

```bash
uv run script.py
```

uv automatically creates an isolated environment with the dependencies!

## Project Workflows

### Starting a New Project

```bash
# 1. Initialize project
uv init my-electricity-project
cd my-electricity-project

# 2. Add dependencies
uv add pandas numpy matplotlib entsoe-py python-dotenv

# 3. Add dev dependencies
uv add --dev pytest black ruff

# 4. Create your code
mkdir -p src/my_electricity_project
touch src/my_electricity_project/__init__.py
touch src/my_electricity_project/main.py

# 5. Run your code
uv run python src/my_electricity_project/main.py
```

### Working with Existing Projects

#### Option A: Project with pyproject.toml

```bash
# Clone repository
git clone https://github.com/user/project.git
cd project

# Install dependencies (creates venv automatically)
uv sync

# Run tests
uv run pytest

# Run application
uv run python -m myapp
```

#### Option B: Project with requirements.txt

```bash
# Create virtual environment
uv venv

# Activate
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Run your code
python main.py
```

### Migrating from pip/Poetry/Conda

#### From pip + requirements.txt

```bash
# Your existing workflow works as-is!
uv pip install -r requirements.txt

# Or upgrade to modern approach
uv init --no-readme
# Move dependencies to pyproject.toml
uv add $(cat requirements.txt)
```

#### From Poetry

```bash
# uv reads pyproject.toml automatically
uv sync

# Or convert poetry.lock
uv pip compile pyproject.toml -o requirements.txt
```

#### From Conda environment.yml

```bash
# Extract pip dependencies from environment.yml
# Then use uv
uv pip install package1 package2 package3
```

## Lock Files and Reproducibility

### Creating Lock Files

```bash
# Method 1: Using pip compile
uv pip compile requirements.in -o requirements.lock

# Method 2: Using project (creates uv.lock automatically)
uv lock

# Lock with specific Python version
uv lock --python-version 3.12
```

### Using Lock Files

```bash
# Install exact versions from lock
uv pip sync requirements.lock

# Or with uv projects
uv sync --locked
```

### Updating Dependencies

```bash
# Update all dependencies to latest compatible versions
uv lock --upgrade

# Update specific package
uv lock --upgrade-package pandas

# Update and sync
uv sync --upgrade
```

## Configuration

### pyproject.toml Structure

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "France electricity data analysis"
requires-python = ">=3.9"
dependencies = [
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "matplotlib>=3.7.0",
    "entsoe-py>=0.5.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
]

[tool.uv.sources]
# Use local path for development
# my-library = { path = "../my-library" }
```

### requirements.in Format

```txt
# requirements.in - High-level dependencies

# Data processing
pandas>=2.0.0
numpy>=1.24.0

# API access
entsoe-py>=0.5.0
requests>=2.31.0

# Visualization
matplotlib>=3.7.0

# Configuration
python-dotenv>=1.0.0
```

Compile to get exact versions:

```bash
uv pip compile requirements.in -o requirements.txt
```

## Advanced Features

### Override Dependencies

```bash
# Override a specific package version
uv pip install --override overrides.txt -r requirements.txt

# overrides.txt
numpy==1.24.0
```

### Platform-Specific Dependencies

```toml
[project]
dependencies = [
    "pandas>=2.0.0",
    "pywin32>=306 ; sys_platform == 'win32'",
    "uvloop>=0.17.0 ; sys_platform != 'win32'",
]
```

### Workspace Support

For monorepos with multiple packages:

```toml
# Root pyproject.toml
[tool.uv.workspace]
members = ["packages/*"]

# Each package has its own pyproject.toml
# packages/api/pyproject.toml
# packages/worker/pyproject.toml
```

```bash
# Work on specific package
cd packages/api
uv sync

# Sync entire workspace
uv sync --workspace
```

### Resolution Strategies

```bash
# Prefer lowest compatible versions
uv pip compile requirements.in --resolution lowest

# Prefer lowest direct dependencies, highest transitive
uv pip compile requirements.in --resolution lowest-direct
```

### Build from Source

```bash
# Force build from source (no wheels)
uv pip install --no-binary :all: package_name

# Build specific package from source
uv pip install --no-binary pandas pandas
```

## Performance Tips

### Global Cache

uv uses a global cache to avoid re-downloading packages:

```bash
# Cache location
uv cache dir

# Clean cache
uv cache clean

# Clean specific package
uv cache clean pandas
```

### Parallel Installation

uv automatically installs packages in parallel for maximum speed.

### Warm Cache Benefits

After first install, subsequent operations are 80-115x faster due to caching.

## Common Patterns

### Development Setup

```bash
# Create project
uv init myproject
cd myproject

# Add runtime dependencies
uv add pandas numpy requests

# Add dev dependencies
uv add --dev pytest black ruff mypy

# Create .env file for secrets
cat > .env << EOF
API_KEY=your-secret-key
DATABASE_URL=postgresql://localhost/mydb
EOF

# Run tests
uv run pytest

# Format code
uv run black src/

# Lint code
uv run ruff check src/
```

### CI/CD Pipeline

```bash
# Install uv in CI
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create reproducible environment
uv venv
uv pip sync requirements.lock

# Run tests
uv run pytest
```

### Docker Integration

```dockerfile
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Run application
CMD ["uv", "run", "python", "-m", "myapp"]
```

## Environment Variables

```bash
# Disable automatic Python downloads
export UV_PYTHON_DOWNLOADS=never

# Set custom cache directory
export UV_CACHE_DIR=/path/to/cache

# Enable verbose output
export UV_VERBOSE=1

# Use system Python only
export UV_NO_MANAGED_PYTHON=1

# Set custom index URL
export UV_INDEX_URL=https://pypi.org/simple
```

## Troubleshooting

### Python Not Found

```bash
# Let uv install Python automatically
uv python install 3.12

# Or specify system Python explicitly
uv venv --python /usr/bin/python3.12
```

### Dependency Conflicts

```bash
# Show detailed resolution
uv pip install package_name --verbose

# Use override file for conflicts
echo "conflicting-package==1.0.0" > overrides.txt
uv pip install -r requirements.txt --override overrides.txt
```

### Cache Issues

```bash
# Clear cache and reinstall
uv cache clean
uv pip install -r requirements.txt
```

### Virtual Environment Issues

```bash
# Delete and recreate venv
rm -rf .venv
uv venv
uv sync
```

## Comparison with Other Tools

| Feature | uv | pip | Poetry | Conda |
|---------|-----|-----|--------|-------|
| Installation Speed | ⚡ 10-100x faster | Baseline | ~2x slower | ~5x slower |
| Virtual Environments | ✅ Built-in | ❌ Separate tool | ✅ Built-in | ✅ Built-in |
| Python Management | ✅ Yes | ❌ No | ❌ No | ✅ Yes |
| Lock Files | ✅ Yes | ❌ Needs pip-tools | ✅ Yes | ✅ Yes |
| Dependency Resolution | ✅ Advanced | ❌ Basic | ✅ Advanced | ✅ Advanced |
| Disk Space | ✅ Shared cache | ❌ Duplicates | ❌ Duplicates | ❌ Large envs |
| pip Compatible | ✅ Drop-in | N/A | ❌ Different | ❌ Different |
| Speed (venv) | ⚡ 80x faster | Baseline | Similar | Similar |
| Tool Management | ✅ Built-in | ❌ Needs pipx | ❌ No | ❌ No |

## Best Practices

### 1. Use pyproject.toml for New Projects

```bash
uv init myproject
cd myproject
uv add dependencies
```

### 2. Pin Python Version

```bash
# Create .python-version file
uv python pin 3.12
```

### 3. Use Lock Files for Reproducibility

```bash
# Generate lock file
uv lock

# Commit uv.lock to version control
git add uv.lock
git commit -m "Add dependency lock file"

# On other machines
uv sync --frozen
```

### 4. Separate Dev Dependencies

```bash
uv add --dev pytest black ruff mypy
```

### 5. Use .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual environments
.venv/
venv/
ENV/

# uv
.uv/

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
```

### 6. Keep uv Updated

```bash
# Regular updates for latest features
uv self update
```


## Resources

- **Official Documentation**: https://docs.astral.sh/uv/
- **GitHub Repository**: https://github.com/astral-sh/uv
- **Discord Community**: https://discord.gg/astral-sh
- **Real Python Tutorial**: https://realpython.com/python-uv/
- **Charlie Marsh's Talk**: Search "uv python" on YouTube

## Integration Examples

### With Jupyter Notebooks

```bash
# Create project
uv init data-analysis
cd data-analysis

# Add Jupyter and data science packages
uv add jupyter pandas numpy matplotlib

# Run Jupyter
uv run jupyter notebook
```

### With FastAPI

```bash
# Create project
uv init api-project
cd api-project

# Add FastAPI dependencies
uv add fastapi uvicorn[standard]

# Run server
uv run uvicorn main:app --reload
```

### With Django

```bash
# Create project
uv init mysite
cd mysite

# Add Django
uv add django

# Start project
uv run django-admin startproject config .

# Run development server
uv run python manage.py runserver
```

