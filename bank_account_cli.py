import argparse
import logging
import sqlite3
from pathlib import Path
import sys

DB_PATH = Path("bank.db")
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "bank_account_cli.log"

LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("bank_account_cli")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(message)s")
console_handler.setFormatter(console_formatter)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setLevel(logging.WARNING)
file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
file_handler.setFormatter(file_formatter)

if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


class Customer:
    """Data class representing a customer."""

    def __init__(self, customer_id: str, first_name: str, last_name: str, address: str | None = None):
        self.customer_id = customer_id
        self.first_name = first_name
        self.last_name = last_name
        self.address = address or ""

    @classmethod
    def from_row(cls, row: tuple[str, str, str, str]):
        return cls(*row)


class Account:
    """Data class representing a bank account."""

    VALID_ACCOUNT_TYPES = {"checking", "savings"}

    def __init__(self, account_id: str, customer_id: str, account_type: str, balance: float = 0.0):
        self.account_id = account_id
        self.customer_id = customer_id
        self.account_type = account_type
        self.balance = balance

    @classmethod
    def from_row(cls, row: tuple[str, str, str, float]):
        return cls(*row)


class BankDB:
    """Database layer for customers and accounts."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def init_db(self) -> None:
        """Create the customers and accounts tables if they do not exist."""
        with sqlite3.connect(self.db_path) as conn:
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

    @staticmethod
    def normalize_account_type(account_type: str) -> str:
        """Normalize and validate account type."""
        normalized = account_type.strip().lower()
        if normalized not in Account.VALID_ACCOUNT_TYPES:
            raise ValueError("Account type must be 'checking' or 'savings'.")
        return normalized

    def get_customer(self, customer_id: str) -> Customer | None:
        """Fetch a customer from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT customer_id, first_name, last_name, address FROM customers WHERE customer_id = ?",
                (customer_id,),
            )
            row = cursor.fetchone()
        return Customer.from_row(row) if row else None

    def get_account(self, account_id: str) -> Account | None:
        """Fetch an account from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT account_id, customer_id, account_type, balance FROM accounts WHERE account_id = ?",
                (account_id,),
            )
            row = cursor.fetchone()
        return Account.from_row(row) if row else None

    def create_customer(self, customer: Customer) -> None:
        """Insert a new customer into the database."""
        if not all([customer.customer_id, customer.first_name, customer.last_name]):
            raise ValueError("Customer ID, first name, and last name are required.")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO customers (customer_id, first_name, last_name, address) VALUES (?, ?, ?, ?)",
                (customer.customer_id.strip(), customer.first_name.strip(), customer.last_name.strip(), customer.address.strip()),
            )

    def create_account(self, account: Account) -> None:
        """Insert a new account into the database."""
        account.account_type = self.normalize_account_type(account.account_type)
        if account.balance < 0:
            raise ValueError("Initial balance cannot be negative.")
        if not self.get_customer(account.customer_id):
            raise ValueError(f"No customer found with id '{account.customer_id}'.")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO accounts (account_id, customer_id, account_type, balance) VALUES (?, ?, ?, ?)",
                (account.account_id.strip(), account.customer_id.strip(), account.account_type, account.balance),
            )

    def deposit(self, account_id: str, amount: float) -> float:
        """Deposit money into an existing account."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        account = self.get_account(account_id)
        if not account:
            raise ValueError(f"No account found with id '{account_id}'.")
        new_balance = account.balance + amount
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE accounts SET balance = ? WHERE account_id = ?", (new_balance, account_id))
        return new_balance

    def withdraw(self, account_id: str, amount: float) -> float:
        """Withdraw money from an existing account."""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        account = self.get_account(account_id)
        if not account:
            raise ValueError(f"No account found with id '{account_id}'.")
        if amount > account.balance:
            raise ValueError("Insufficient funds.")
        new_balance = account.balance - amount
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE accounts SET balance = ? WHERE account_id = ?", (new_balance, account_id))
        return new_balance

    def loan_service(self, customer_id: str, service_id: str, service_name: str, amount: float) -> str:
        """Process a loan request for a customer."""
        if amount <= 0:
            raise ValueError("Loan amount must be positive.")
        if not self.get_customer(customer_id):
            raise ValueError(f"No customer found with id '{customer_id}'.")
        return f"Loan #{service_id} ({service_name}) of {amount:.2f} for customer {customer_id} has been processed."

    def credit_card_service(self, customer_id: str, credit_limit: float) -> str:
        """Issue a credit card to a customer."""
        if credit_limit <= 0:
            raise ValueError("Credit limit must be positive.")
        if not self.get_customer(customer_id):
            raise ValueError(f"No customer found with id '{customer_id}'.")
        return f"Credit card with a limit of {credit_limit:.2f} has been issued to customer {customer_id}."

    def list_accounts(self, account_type: str | None = None, customer_id: str | None = None) -> list[Account]:
        """List accounts with optional filtering."""
        query = "SELECT account_id, customer_id, account_type, balance FROM accounts"
        params: list[str] = []
        conditions: list[str] = []
        if account_type:
            conditions.append("account_type = ?")
            params.append(self.normalize_account_type(account_type))
        if customer_id:
            conditions.append("customer_id = ?")
            params.append(customer_id)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY account_id"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
        return [Account.from_row(row) for row in rows]

    def list_customers(self, account_type: str | None = None) -> list[Customer]:
        """List customers, optionally filtered by account type."""
        if account_type:
            normalized_type = self.normalize_account_type(account_type)
            query = """
                SELECT DISTINCT c.customer_id, c.first_name, c.last_name, c.address
                FROM customers c
                JOIN accounts a ON c.customer_id = a.customer_id
                WHERE a.account_type = ?
                ORDER BY c.customer_id
                """
            params = (normalized_type,)
        else:
            query = "SELECT customer_id, first_name, last_name, address FROM customers ORDER BY customer_id"
            params = ()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
        return [Customer.from_row(row) for row in rows]


class BankCLI:
    """Command-line interface for BankDB operations."""

    def __init__(self, db: BankDB):
        self.db = db

    @staticmethod
    def prompt_yes_no(message: str, default: bool = False) -> bool:
        """Prompt the user for a yes/no answer."""
        default_text = "Y/n" if default else "y/N"
        answer = input(f"{message} ({default_text}): ").strip().lower()
        if not answer:
            return default
        return answer in {"y", "yes"}

    @staticmethod
    def prompt_for_customer_data() -> Customer:
        """Collect customer data from the user."""
        customer_id = input("Customer ID: ").strip()
        first_name = input("First name: ").strip()
        last_name = input("Last name: ").strip()
        address = input("Address (optional): ").strip()
        return Customer(customer_id, first_name, last_name, address)

    @staticmethod
    def prompt_for_account_data() -> Account:
        """Collect account data from the user."""
        account_id = input("Account ID: ").strip()
        customer_id = input("Customer ID: ").strip()
        account_type = input("Account type (checking/savings): ").strip()
        initial_balance_raw = input("Initial balance (default 0): ").strip() or "0"
        try:
            initial_balance = float(initial_balance_raw)
        except ValueError:
            raise ValueError("Initial balance must be a valid number.")
        return Account(account_id, customer_id, account_type, initial_balance)

    @staticmethod
    def prompt_for_transaction_data() -> tuple[str, str, float]:
        """Collect deposit or withdrawal data from the user."""
        action = input("Transaction type (deposit/withdraw): ").strip().lower()
        if action not in {"deposit", "withdraw"}:
            raise ValueError("Transaction type must be 'deposit' or 'withdraw'.")
        account_id = input("Account ID: ").strip()
        amount_raw = input("Amount: ").strip()
        try:
            amount = float(amount_raw)
        except ValueError:
            raise ValueError("Amount must be a valid number.")
        return action, account_id, amount

    @staticmethod
    def prompt_for_loan_data() -> tuple[str, str, str, float]:
        """Collect loan request data from the user."""
        customer_id = input("Customer ID: ").strip()
        service_id = input("Loan ID: ").strip()
        service_name = input("Loan service name: ").strip()
        amount_raw = input("Loan amount: ").strip()
        try:
            amount = float(amount_raw)
        except ValueError:
            raise ValueError("Loan amount must be a valid number.")
        return customer_id, service_id, service_name, amount

    @staticmethod
    def prompt_for_credit_card_data() -> tuple[str, float]:
        """Collect credit card request data from the user."""
        customer_id = input("Customer ID: ").strip()
        credit_limit_raw = input("Credit limit: ").strip()
        try:
            credit_limit = float(credit_limit_raw)
        except ValueError:
            raise ValueError("Credit limit must be a valid number.")
        return customer_id, credit_limit

    def interactive_menu(self) -> int:
        """Run the interactive CLI menu."""
        while True:
            print("\nBank Account CLI")
            print("1) Create customer")
            print("2) Create account")
            print("3) Conduct transaction (deposit or withdraw)")
            print("4) Request a loan")
            print("5) Issue a credit card")
            print("6) List accounts")
            print("7) List customers")
            print("8) List customers by account type")
            print("9) Exit")

            choice = input("Choose an option [1-9]: ").strip()
            try:
                if choice == "1":
                    customer = self.prompt_for_customer_data()
                    self.db.create_customer(customer)
                    print(f"Customer '{customer.customer_id}' created.")
                elif choice == "2":
                    account = self.prompt_for_account_data()
                    if not self.db.get_customer(account.customer_id):
                        print(f"Customer '{account.customer_id}' does not exist.")
                        if self.prompt_yes_no("Create a new customer for this account?", default=False):
                            customer = self.prompt_for_customer_data()
                            if customer.customer_id != account.customer_id:
                                print("Warning: entered customer ID does not match the account customer ID.")
                            self.db.create_customer(customer)
                            print(f"Customer '{customer.customer_id}' created.")
                    self.db.create_account(account)
                    print(f"Account '{account.account_id}' created for customer '{account.customer_id}'.")
                elif choice == "3":
                    action, account_id, amount = self.prompt_for_transaction_data()
                    if action == "deposit":
                        new_balance = self.db.deposit(account_id, amount)
                        print(f"Deposited {amount:.2f} into {account_id}. New balance: {new_balance:.2f}")
                    else:
                        new_balance = self.db.withdraw(account_id, amount)
                        print(f"Withdrew {amount:.2f} from {account_id}. New balance: {new_balance:.2f}")
                elif choice == "4":
                    customer_id, service_id, service_name, amount = self.prompt_for_loan_data()
                    message = self.db.loan_service(customer_id, service_id, service_name, amount)
                    print(message)
                elif choice == "5":
                    customer_id, credit_limit = self.prompt_for_credit_card_data()
                    message = self.db.credit_card_service(customer_id, credit_limit)
                    print(message)
                elif choice == "6":
                    account_type = input("Filter by account type (checking/savings) or leave blank: ").strip() or None
                    customer_id = input("Filter by customer ID or leave blank: ").strip() or None
                    accounts = self.db.list_accounts(account_type, customer_id)
                    if not accounts:
                        print("No accounts found.")
                    else:
                        print("Accounts:")
                        for account in accounts:
                            print(f"- {account.account_id} | customer: {account.customer_id} | type: {account.account_type} | balance: {account.balance:.2f}")
                elif choice == "7":
                    account_type = input("Filter customers by account type (checking/savings) or leave blank: ").strip() or None
                    customers = self.db.list_customers(account_type)
                    if not customers:
                        print("No customers found.")
                    else:
                        print("Customers:")
                        for customer in customers:
                            print(f"- {customer.customer_id} | {customer.first_name} {customer.last_name} | address: {customer.address}")
                elif choice == "8":
                    account_type = input("Account type to filter by (checking/savings): ").strip()
                    customers = self.db.list_customers(account_type)
                    if not customers:
                        print(f"No customers found with account type '{account_type}'.")
                    else:
                        print(f"Customers with {account_type} accounts:")
                        for customer in customers:
                            print(f"- {customer.customer_id} | {customer.first_name} {customer.last_name} | address: {customer.address}")
                elif choice == "9":
                    print("Goodbye!")
                    return 0
                else:
                    logger.warning("Invalid menu choice: %s", choice)
                    print("Invalid choice. Enter 1-9.")
            except sqlite3.IntegrityError as exc:
                logger.error("Database error: %s", exc, exc_info=True)
                print(f"Database error: {exc}")
            except ValueError as exc:
                logger.error("Error: %s", exc)
                print(f"Error: {exc}")
            except Exception as exc:
                logger.error("Unexpected error: %s", exc, exc_info=True)
                print("An unexpected error occurred. Please check the log file for details.")
            if not self.prompt_yes_no("Would you like to perform another action?", default=True):
                return 0

    def process_command(self, args: argparse.Namespace) -> int:
        """Process parsed command-line arguments."""
        if args.command == "create-customer":
            customer = Customer(args.customer_id, args.first_name, args.last_name, args.address)
            self.db.create_customer(customer)
            print(f"Customer '{customer.customer_id}' created or already exists.")
            return 0

        if args.command == "create-account":
            if not self.db.get_customer(args.customer_id):
                if args.create_customer_if_missing:
                    if not args.customer_first_name or not args.customer_last_name:
                        raise ValueError("Provide --customer-first-name and --customer-last-name to create a missing customer.")
                    new_customer = Customer(args.customer_id, args.customer_first_name, args.customer_last_name, args.customer_address)
                    self.db.create_customer(new_customer)
                    print(f"Customer '{new_customer.customer_id}' created.")
                else:
                    raise ValueError(f"Customer '{args.customer_id}' not found. Use --create-customer-if-missing to create it.")
            account = Account(args.account_id, args.customer_id, args.account_type, args.initial_balance)
            self.db.create_account(account)
            print("Account created:")
            print(f"  account_id: {account.account_id}")
            print(f"  customer_id: {account.customer_id}")
            print(f"  account_type: {account.account_type}")
            print(f"  balance: {account.balance:.2f}")
            return 0

        if args.command == "deposit":
            new_balance = self.db.deposit(args.account_id, args.amount)
            print(f"Deposited {args.amount:.2f} into account '{args.account_id}'. New balance: {new_balance:.2f}")
            return 0

        if args.command == "withdraw":
            new_balance = self.db.withdraw(args.account_id, args.amount)
            print(f"Withdrew {args.amount:.2f} from account '{args.account_id}'. New balance: {new_balance:.2f}")
            return 0

        if args.command == "loan":
            message = self.db.loan_service(args.customer_id, args.service_id, args.service_name, args.amount)
            print(message)
            return 0

        if args.command == "credit-card":
            message = self.db.credit_card_service(args.customer_id, args.credit_limit)
            print(message)
            return 0

        if args.command == "list-accounts":
            accounts = self.db.list_accounts(args.account_type, args.customer_id)
            if not accounts:
                print("No accounts found.")
                return 0
            print("Accounts:")
            for account in accounts:
                print(f"- {account.account_id} | customer: {account.customer_id} | type: {account.account_type} | balance: {account.balance:.2f}")
            return 0

        if args.command == "list-customers":
            customers = self.db.list_customers(args.account_type)
            if not customers:
                print("No customers found.")
                return 0
            print("Customers:")
            for customer in customers:
                print(f"- {customer.customer_id} | {customer.first_name} {customer.last_name} | address: {customer.address}")
            return 0

        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bank account table CLI for customer, account, and transaction management.")
    subparsers = parser.add_subparsers(dest="command")

    customer_parser = subparsers.add_parser("create-customer", help="Create a new customer.")
    customer_parser.add_argument("--customer-id", required=True, help="Unique customer identifier.")
    customer_parser.add_argument("--first-name", required=True, help="Customer first name.")
    customer_parser.add_argument("--last-name", required=True, help="Customer last name.")
    customer_parser.add_argument("--address", required=False, default="", help="Customer address.")

    account_parser = subparsers.add_parser("create-account", help="Create a new account.")
    account_parser.add_argument("--account-id", required=True, help="Unique account identifier.")
    account_parser.add_argument("--customer-id", required=True, help="Customer identifier for the account.")
    account_parser.add_argument("--account-type", required=True, choices=sorted(Account.VALID_ACCOUNT_TYPES), help="Account type: checking or savings.")
    account_parser.add_argument("--initial-balance", type=float, default=0.0, help="Starting account balance.")
    account_parser.add_argument("--create-customer-if-missing", action="store_true", help="Automatically create the customer if the customer does not exist.")
    account_parser.add_argument("--customer-first-name", required=False, help="First name to create a missing customer.")
    account_parser.add_argument("--customer-last-name", required=False, help="Last name to create a missing customer.")
    account_parser.add_argument("--customer-address", required=False, default="", help="Address to create a missing customer.")

    deposit_parser = subparsers.add_parser("deposit", help="Deposit money into an account.")
    deposit_parser.add_argument("--account-id", required=True, help="Account identifier.")
    deposit_parser.add_argument("--amount", required=True, type=float, help="Amount to deposit.")

    withdraw_parser = subparsers.add_parser("withdraw", help="Withdraw money from an account.")
    withdraw_parser.add_argument("--account-id", required=True, help="Account identifier.")
    withdraw_parser.add_argument("--amount", required=True, type=float, help="Amount to withdraw.")

    loan_parser = subparsers.add_parser("loan", help="Request a loan for a customer.")
    loan_parser.add_argument("--customer-id", required=True, help="Customer identifier.")
    loan_parser.add_argument("--service-id", required=True, help="Loan service identifier.")
    loan_parser.add_argument("--service-name", required=True, help="Loan service name.")
    loan_parser.add_argument("--amount", required=True, type=float, help="Loan amount.")

    credit_card_parser = subparsers.add_parser("credit-card", help="Issue a credit card to a customer.")
    credit_card_parser.add_argument("--customer-id", required=True, help="Customer identifier.")
    credit_card_parser.add_argument("--credit-limit", required=True, type=float, help="Credit limit amount.")

    list_accounts_parser = subparsers.add_parser("list-accounts", help="List all accounts.")
    list_accounts_parser.add_argument("--account-type", required=False, choices=sorted(Account.VALID_ACCOUNT_TYPES), help="Filter accounts by type.")
    list_accounts_parser.add_argument("--customer-id", required=False, help="Filter accounts by customer ID.")

    list_customers_parser = subparsers.add_parser("list-customers", help="List customers.")
    list_customers_parser.add_argument("--account-type", required=False, choices=sorted(Account.VALID_ACCOUNT_TYPES), help="Show customers with this account type.")

    parser.add_argument("--db-path", default=str(DB_PATH), help="Path to the SQLite database file.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    db_path = Path(args.db_path)
    db = BankDB(db_path)
    cli = BankCLI(db)
    if not getattr(args, "command", None):
        return cli.interactive_menu()
    try:
        return cli.process_command(args)
    except sqlite3.IntegrityError as exc:
        logger.error("Database error: %s", exc, exc_info=True)
        print(f"Database error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        logger.error("Error: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        logger.error("Unexpected error: %s", exc, exc_info=True)
        print("An unexpected error occurred. Check logs for details.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
