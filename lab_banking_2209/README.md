# Banking Laboratory (SOFT-753)

Simple banking system built with Python OOP: bank accounts, customers, logging, and a text menu.

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)

## Setup

From this folder (`lab_banking_2209`):

```bash
uv sync
```

## Run the menu

```bash
uv run python -m src.banking
```

Or run the file directly:

```bash
uv run python src/banking.py
```

Menu options:

1. Add customer  
2. Add account  
3. Deposit  
4. Withdraw  
5. Transfer  
6. Total balance  
7. Convert currency  
0. Exit  

Logs are written under `logs/banking.log` (rotated daily).

## Run tests

```bash
uv run pytest
```

## Check code style

```bash
uv run ruff check .
uv run ruff format .
```

## Project layout

```text
lab_banking_2209/
  src/
    banking.py      # BankAccount, Customer, menu
  tests/
    test_banking.py
  logs/
  pyproject.toml
  README.md
```
