# Bank Account CLI Documentation

## Overview

`bank_account_cli.py` provides a class-based command-line interface for managing customers, bank accounts, and basic banking services using a local SQLite database.

The implementation is organized into three main classes:

- `Customer`: Represents a customer record.
- `Account`: Represents a bank account record and enforces valid account types (`checking` or `savings`).
- `BankDB`: Encapsulates SQLite database operations, validation, and business logic.
- `BankCLI`: Handles interactive prompts and command-line argument processing.

The CLI supports both interactive mode and single-command execution.

## Architecture

### Customer

The `Customer` class is a simple data class with the following fields:

- `customer_id`
- `first_name`
- `last_name`
- `address`

It also includes a helper method:

- `from_row(row)`: Builds a `Customer` instance from a database row.

### Account

The `Account` class is a data class representing a bank account. It includes:

- `account_id`
- `customer_id`
- `account_type`
- `balance`

Valid account types are restricted to:

- `checking`
- `savings`

It also provides:

- `from_row(row)`: Builds an `Account` instance from a database row.

### BankDB

`BankDB` is the database layer and provides the following responsibilities:

- Initialize the SQLite database and tables.
- Validate account types and transaction data.
- Insert and query customers and accounts.
- Perform deposits, withdrawals, loan requests, and credit card issuance.
- List accounts and customers with optional filtering.

Key methods include:

- `init_db()`
- `normalize_account_type(account_type)`
- `get_customer(customer_id)`
- `get_account(account_id)`
- `create_customer(customer)`
- `create_account(account)`
- `deposit(account_id, amount)`
- `withdraw(account_id, amount)`
- `loan_service(customer_id, service_id, service_name, amount)`
- `credit_card_service(customer_id, credit_limit)`
- `list_accounts(account_type=None, customer_id=None)`
- `list_customers(account_type=None)`

### BankCLI

`BankCLI` wraps `BankDB` for user interaction and argument parsing. It supports:

- Interactive menu-driven workflows
- Command-line commands
- Validation of numeric values
- Confirmation prompts for retries

## Usage

Run the script with Python from the project folder:

```powershell
python bank_account_cli.py --help
```

### Interactive Mode

If the script is executed without a command, it opens an interactive menu.

```powershell
python bank_account_cli.py
```

### Command Mode

Supported commands:

- `create-customer`
- `create-account`
- `deposit`
- `withdraw`
- `loan`
- `credit-card`
- `list-accounts`
- `list-customers`

#### Create a customer

```powershell
python bank_account_cli.py create-customer --customer-id C001 --first-name Alice --last-name Smith --address "123 Main St"
```

#### Create an account

```powershell
python bank_account_cli.py create-account --account-id A001 --customer-id C001 --account-type checking --initial-balance 100.00
```

If the customer does not exist yet, use:

```powershell
python bank_account_cli.py create-account --account-id A002 --customer-id C002 --account-type savings --initial-balance 500.00 --create-customer-if-missing --customer-first-name Bob --customer-last-name Jones --customer-address "456 Oak Ave"
```

#### Deposit funds

```powershell
python bank_account_cli.py deposit --account-id A001 --amount 50.00
```

#### Withdraw funds

```powershell
python bank_account_cli.py withdraw --account-id A001 --amount 25.00
```

#### Request a loan

```powershell
python bank_account_cli.py loan --customer-id C001 --service-id L001 --service-name "Home Loan" --amount 10000.00
```

#### Issue a credit card

```powershell
python bank_account_cli.py credit-card --customer-id C001 --credit-limit 5000.00
```

#### List accounts

```powershell
python bank_account_cli.py list-accounts
python bank_account_cli.py list-accounts --account-type checking
python bank_account_cli.py list-accounts --customer-id C001
```

#### List customers

```powershell
python bank_account_cli.py list-customers
python bank_account_cli.py list-customers --account-type savings
```

## Database file

The default SQLite file is `bank.db` in the current directory. Use `--db-path` to override it:

```powershell
python bank_account_cli.py --db-path custom_bank.db list-accounts
```

## Notes

- Account types are normalized and validated by `BankDB.normalize_account_type`.
- `create_account` requires the customer to exist unless `--create-customer-if-missing` is provided.
- Deposits and withdrawals enforce positive amounts.
- Loan and credit card services are simulated with return messages; they do not create additional database records.
