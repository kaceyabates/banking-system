# Bank Account CLI

This CLI script provides a fully functional interface for managing customers, accounts, and transactions in `bank.db`.

## Supported commands

- `create-customer` — Create a new customer.
- `create-account` — Create a new account for an existing customer, or create the customer automatically when requested.
- `deposit` — Deposit funds into an existing account.
- `withdraw` — Withdraw funds from an existing account.
- `loan` — Request a loan for a customer.
- `credit-card` — Issue a credit card to a customer.
- `list-accounts` — List accounts, with optional filters.
- `list-customers` — List customers, optionally filtered by account type.

## Interactive mode

Run the script without a command to use the interactive menu:

```powershell
python bank_account_cli.py
```

Then choose one of the numbered options:

1) Create customer
2) Create account
3) Conduct transaction (deposit or withdraw)
4) Request a loan
5) Issue a credit card
6) List accounts
7) List customers
8) List customers by account type
9) Exit

Interactive mode will let you create customers, create accounts, make deposits or withdrawals, and view filtered records.

## Command examples

Create a customer:

```powershell
python bank_account_cli.py create-customer --customer-id C001 --first-name Jane --last-name Doe --address "123 Main St"
```

Create an account for an existing customer:

```powershell
python bank_account_cli.py create-account --account-id A001 --customer-id C001 --account-type checking --initial-balance 100.00
```

Create an account and automatically create a missing customer:

```powershell
python bank_account_cli.py create-account --account-id A002 --customer-id C002 --account-type savings --initial-balance 500.00 --create-customer-if-missing --customer-first-name Alice --customer-last-name Smith --customer-address "456 Elm St"
```

Deposit funds:

```powershell
python bank_account_cli.py deposit --account-id A001 --amount 50.00
```

Withdraw funds:

```powershell
python bank_account_cli.py withdraw --account-id A001 --amount 25.00
```

Request a loan:

```powershell
python bank_account_cli.py loan --customer-id C001 --service-id L001 --service-name "Personal Loan" --amount 1000.00
```

Issue a credit card:

```powershell
python bank_account_cli.py credit-card --customer-id C001 --credit-limit 5000.00
```

List all accounts:

```powershell
python bank_account_cli.py list-accounts
```

List accounts by type:

```powershell
python bank_account_cli.py list-accounts --account-type savings
```

List customers with a specific account type:

```powershell
python bank_account_cli.py list-customers --account-type checking
```

## Notes

- Account type is strictly limited to `checking` or `savings`.
- If the customer does not exist, use `--create-customer-if-missing` with customer information when creating an account.
- The default database file is `bank.db` in the current working directory.
- Use `--db-path` to point to a different database file.
