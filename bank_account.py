import argparse
import os
import sqlite3
import sys

DB_FILE = os.path.join(os.getcwd(), "bank.db")

def ensure_db():
    # Create required tables if they do not exist yet
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            address TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            account_type TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        )
        """
    )
    conn.commit()
    conn.close()


def normalize_account_type(value):
    if not value:
        raise ValueError("Account type is required.")
    value = value.strip().lower()
    if value not in ("checking", "savings"):
        raise ValueError("Account type must be checking or savings.")
    return value


def run_query(sql, args=(), fetch=False):
    # Centralized DB helper so commands share one execute/fetch flow
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(sql, args)
    rows = cur.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return rows


def get_customer(customer_id):
    rows = run_query(
        "SELECT customer_id, first_name, last_name, address FROM customers WHERE customer_id = ?",
        (customer_id,),
        fetch=True,
    )
    return rows[0] if rows else None


def get_account(account_id):
    rows = run_query(
        "SELECT account_id, customer_id, account_type, balance FROM accounts WHERE account_id = ?",
        (account_id,),
        fetch=True,
    )
    return rows[0] if rows else None


def create_customer(customer_id, first_name, last_name, address):
    if not customer_id or not first_name or not last_name:
        raise ValueError("Customer ID, first name and last name are required.")
    run_query(
        "INSERT OR IGNORE INTO customers (customer_id, first_name, last_name, address) VALUES (?, ?, ?, ?)",
        (customer_id.strip(), first_name.strip(), last_name.strip(), address.strip()),
    )


def create_account(account_id, customer_id, account_type, balance):
    account_type = normalize_account_type(account_type)
    if balance < 0:
        raise ValueError("Initial balance cannot be negative.")
    if not get_customer(customer_id):
        raise ValueError("Customer %s does not exist." % customer_id)
    run_query(
        "INSERT INTO accounts (account_id, customer_id, account_type, balance) VALUES (?, ?, ?, ?)",
        (account_id.strip(), customer_id.strip(), account_type, balance),
    )


def deposit(account_id, amount):
    if amount <= 0:
        raise ValueError("Deposit amount must be positive.")
    account = get_account(account_id)
    if not account:
        raise ValueError("Account %s not found." % account_id)
    new_balance = account[3] + amount
    run_query("UPDATE accounts SET balance = ? WHERE account_id = ?", (new_balance, account_id))
    return new_balance


def withdraw(account_id, amount):
    if amount <= 0:
        raise ValueError("Withdrawal amount must be positive.")
    account = get_account(account_id)
    if not account:
        raise ValueError("Account %s not found." % account_id)
    if amount > account[3]:
        raise ValueError("Insufficient funds.")
    new_balance = account[3] - amount
    run_query("UPDATE accounts SET balance = ? WHERE account_id = ?", (new_balance, account_id))
    return new_balance


def loan_service(customer_id, service_id, service_name, amount):
    if amount <= 0:
        raise ValueError("Loan amount must be positive.")
    if not get_customer(customer_id):
        raise ValueError("Customer %s not found." % customer_id)
    return "Loan #%s (%s) of %.2f for customer %s has been processed." % (
        service_id,
        service_name,
        amount,
        customer_id,
    )


def credit_card_service(customer_id, credit_limit):
    if credit_limit <= 0:
        raise ValueError("Credit limit must be positive.")
    if not get_customer(customer_id):
        raise ValueError("Customer %s not found." % customer_id)
    return "Credit card with a limit of %.2f has been issued to customer %s." % (
        credit_limit,
        customer_id,
    )


def list_accounts(account_type=None, customer_id=None):
    sql = "SELECT account_id, customer_id, account_type, balance FROM accounts"
    args = []
    parts = []
    # Build WHERE filters only for values the user actually passed.
    if account_type:
        parts.append("account_type = ?")
        args.append(normalize_account_type(account_type))
    if customer_id:
        parts.append("customer_id = ?")
        args.append(customer_id)
    if parts:
        sql += " WHERE " + " AND ".join(parts)
    sql += " ORDER BY account_id"
    return run_query(sql, tuple(args), fetch=True)


def list_customers(account_type=None):
    if account_type:
        account_type = normalize_account_type(account_type)
        sql = (
            "SELECT DISTINCT c.customer_id, c.first_name, c.last_name, c.address "
            "FROM customers c JOIN accounts a ON c.customer_id = a.customer_id "
            "WHERE a.account_type = ? ORDER BY c.customer_id"
        )
        return run_query(sql, (account_type,), fetch=True)
    return run_query("SELECT customer_id, first_name, last_name, address FROM customers ORDER BY customer_id", (), fetch=True)


def ask_yes_no(prompt, default=False):
    label = "Y/n" if default else "y/N"
    answer = input("%s (%s): " % (prompt, label)).strip().lower()
    if answer == "":
        return default
    return answer in ("y", "yes")


def read_float(prompt):
    raw = input(prompt).strip()
    if raw == "":
        return 0.0
    try:
        return float(raw)
    except ValueError:
        raise ValueError("Value must be a number.")


def interactive_menu():
    # Interactive mode mirrors the CLI commands for quick manual use
    while True:
        print("\nBank Account CLI")
        print("1) Create customer")
        print("2) Create account")
        print("3) Deposit")
        print("4) Withdraw")
        print("5) Request a loan")
        print("6) Issue a credit card")
        print("7) List accounts")
        print("8) List customers")
        print("9) List customers by account type")
        print("0) Exit")

        choice = input("Choose an option [0-9]: ").strip()

        try:
            if choice == "1":
                customer_id = input("Customer ID: ").strip()
                first_name = input("First name: ").strip()
                last_name = input("Last name: ").strip()
                address = input("Address (optional): ").strip()
                create_customer(customer_id, first_name, last_name, address)
                print("Customer %s created." % customer_id)
            elif choice == "2":
                account_id = input("Account ID: ").strip()
                customer_id = input("Customer ID: ").strip()
                account_type = input("Account type (checking/savings): ").strip()
                balance = read_float("Initial balance (default 0): ")
                if not get_customer(customer_id):
                    print("Customer %s does not exist." % customer_id)
                    if ask_yes_no("Create new customer for this account?", False):
                        customer_id = input("Customer ID: ").strip()
                        first_name = input("First name: ").strip()
                        last_name = input("Last name: ").strip()
                        address = input("Address (optional): ").strip()
                        create_customer(customer_id, first_name, last_name, address)
                        print("Customer %s created." % customer_id)
                create_account(account_id, customer_id, account_type, balance)
                print("Account %s created." % account_id)
            elif choice == "3":
                account_id = input("Account ID: ").strip()
                amount = read_float("Deposit amount: ")
                new_balance = deposit(account_id, amount)
                print("Deposited %.2f into %s. New balance %.2f." % (amount, account_id, new_balance))
            elif choice == "4":
                account_id = input("Account ID: ").strip()
                amount = read_float("Withdraw amount: ")
                new_balance = withdraw(account_id, amount)
                print("Withdrew %.2f from %s. New balance %.2f." % (amount, account_id, new_balance))
            elif choice == "5":
                customer_id = input("Customer ID: ").strip()
                service_id = input("Loan ID: ").strip()
                service_name = input("Loan service name: ").strip()
                amount = read_float("Loan amount: ")
                print(loan_service(customer_id, service_id, service_name, amount))
            elif choice == "6":
                customer_id = input("Customer ID: ").strip()
                credit_limit = read_float("Credit limit: ")
                print(credit_card_service(customer_id, credit_limit))
            elif choice == "7":
                account_type = input("Filter by account type or leave blank: ").strip() or None
                customer_id = input("Filter by customer ID or leave blank: ").strip() or None
                rows = list_accounts(account_type, customer_id)
                if not rows:
                    print("No accounts found.")
                else:
                    print("Accounts:")
                    for row in rows:
                        print("- %s | %s | %s | %.2f" % (row[0], row[1], row[2], row[3]))
            elif choice == "8":
                account_type = input("Filter customers by account type or leave blank: ").strip() or None
                rows = list_customers(account_type)
                if not rows:
                    print("No customers found.")
                else:
                    print("Customers:")
                    for row in rows:
                        print("- %s | %s %s | %s" % (row[0], row[1], row[2], row[3]))
            elif choice == "9":
                account_type = input("Account type to filter by: ").strip()
                rows = list_customers(account_type)
                if not rows:
                    print("No customers found.")
                else:
                    print("Customers with %s accounts:" % account_type)
                    for row in rows:
                        print("- %s | %s %s | %s" % (row[0], row[1], row[2], row[3]))
            elif choice == "0":
                print("Goodbye.")
                return 0
            else:
                print("Invalid choice.")
        except sqlite3.IntegrityError as exc:
            print("Database error: %s" % exc, file=sys.stderr)
        except ValueError as exc:
            print("Error: %s" % exc, file=sys.stderr)
        except Exception as exc:
            print("Unexpected error: %s" % exc, file=sys.stderr)

        if not ask_yes_no("Do another action?", True):
            return 0


def process_command(args):
    # Non-interactive path for scriptable CLI usage
    if args.command == "create-customer":
        create_customer(args.customer_id, args.first_name, args.last_name, args.address)
        print("Customer %s created." % args.customer_id)
        return 0
    if args.command == "create-account":
        if not get_customer(args.customer_id):
            if args.create_customer_if_missing:
                if not args.customer_first_name or not args.customer_last_name:
                    raise ValueError("Missing customer name to create new customer.")
                create_customer(args.customer_id, args.customer_first_name, args.customer_last_name, args.customer_address)
                print("Customer %s created." % args.customer_id)
            else:
                raise ValueError("Customer %s not found." % args.customer_id)
        create_account(args.account_id, args.customer_id, args.account_type, args.initial_balance)
        print("Account %s created." % args.account_id)
        return 0
    if args.command == "deposit":
        new_balance = deposit(args.account_id, args.amount)
        print("Deposited %.2f into %s. New balance %.2f." % (args.amount, args.account_id, new_balance))
        return 0
    if args.command == "withdraw":
        new_balance = withdraw(args.account_id, args.amount)
        print("Withdrew %.2f from %s. New balance %.2f." % (args.amount, args.account_id, new_balance))
        return 0
    if args.command == "loan":
        print(loan_service(args.customer_id, args.service_id, args.service_name, args.amount))
        return 0
    if args.command == "credit-card":
        print(credit_card_service(args.customer_id, args.credit_limit))
        return 0
    if args.command == "list-accounts":
        rows = list_accounts(args.account_type, args.customer_id)
        if not rows:
            print("No accounts found.")
            return 0
        for row in rows:
            print("- %s | %s | %s | %.2f" % (row[0], row[1], row[2], row[3]))
        return 0
    if args.command == "list-customers":
        rows = list_customers(args.account_type)
        if not rows:
            print("No customers found.")
            return 0
        for row in rows:
            print("- %s | %s %s | %s" % (row[0], row[1], row[2], row[3]))
        return 0
    return 1


def build_parser():
    # Keep all command definitions in one place.
    parser = argparse.ArgumentParser(description="Bank account CLI")
    sub = parser.add_subparsers(dest="command")

    cust = sub.add_parser("create-customer")
    cust.add_argument("--customer-id", required=True)
    cust.add_argument("--first-name", required=True)
    cust.add_argument("--last-name", required=True)
    cust.add_argument("--address", default="")

    acct = sub.add_parser("create-account")
    acct.add_argument("--account-id", required=True)
    acct.add_argument("--customer-id", required=True)
    acct.add_argument("--account-type", required=True, choices=["checking", "savings"])
    acct.add_argument("--initial-balance", type=float, default=0.0)
    acct.add_argument("--create-customer-if-missing", action="store_true")
    acct.add_argument("--customer-first-name")
    acct.add_argument("--customer-last-name")
    acct.add_argument("--customer-address", default="")

    dep = sub.add_parser("deposit")
    dep.add_argument("--account-id", required=True)
    dep.add_argument("--amount", required=True, type=float)

    wd = sub.add_parser("withdraw")
    wd.add_argument("--account-id", required=True)
    wd.add_argument("--amount", required=True, type=float)

    loan = sub.add_parser("loan")
    loan.add_argument("--customer-id", required=True)
    loan.add_argument("--service-id", required=True)
    loan.add_argument("--service-name", required=True)
    loan.add_argument("--amount", required=True, type=float)

    card = sub.add_parser("credit-card")
    card.add_argument("--customer-id", required=True)
    card.add_argument("--credit-limit", required=True, type=float)

    list_accts = sub.add_parser("list-accounts")
    list_accts.add_argument("--account-type", choices=["checking", "savings"])
    list_accts.add_argument("--customer-id")

    list_cust = sub.add_parser("list-customers")
    list_cust.add_argument("--account-type", choices=["checking", "savings"])

    return parser


def main():
    ensure_db()
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        return interactive_menu()
    try:
        return process_command(args)
    except sqlite3.IntegrityError as exc:
        print("Database error: %s" % exc, file=sys.stderr)
    except ValueError as exc:
        print("Error: %s" % exc, file=sys.stderr)
    except Exception as exc:
        print("Unexpected error: %s" % exc, file=sys.stderr)
    return 1

if __name__ == "__main__":
    sys.exit(main())
