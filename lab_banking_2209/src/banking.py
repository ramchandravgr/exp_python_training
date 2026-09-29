from datetime import date
from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler

_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
_file_handler = TimedRotatingFileHandler(
    _LOG_DIR / "banking.log",
    when="midnight",
    interval=1,
    backupCount=30,
    encoding="utf-8",
)
_file_handler.suffix = "%Y-%m-%d"
_file_handler.setFormatter(_formatter)
logger.addHandler(_file_handler)


class InsufficientFundsError(Exception):
    def __init__(self, message: str, amount: float):
        super().__init__(message)
        self.message = message
        self.amount = amount


class BankAccount:
    _min_savings_usd = 100.0
    # Simple rates to USD for the savings $100 minimum check
    _rates_to_usd = {"USD": 1.0, "EUR": 1.1, "INR": 1 / 80}

    def __init__(
        self,
        account_number: str,
        currency: str = "USD",
        _account_type: str = "checking",
        balance: float = 0.0,
    ):
        self.account_number = account_number
        self.currency = currency
        self._account_type = _account_type
        if balance < 0:
            logger.error("Balance cannot be negative")
            raise ValueError("Balance cannot be negative")
        self.__balance = float(balance)

    def get_account_number(self) -> str:
        return self.account_number

    def get_currency(self) -> str:
        return self.currency

    def get_account_type(self) -> str:
        return self._account_type

    def get_balance(self) -> float:
        return self.__balance

    def set_balance(self, balance: float) -> None:
        if balance < 0:
            logger.error("Balance cannot be negative")
            raise ValueError("Balance cannot be negative")
        self.__balance = float(balance)

    def _min_balance(self) -> float:
        rate = self._rates_to_usd.get(self.currency)
        if rate is None:
            raise ValueError(f"Unknown currency: {self.currency}")
        return self._min_savings_usd / rate

    def deposit(self, amount: float) -> None:
        if amount < 0:
            logger.error("Amount cannot be negative")
            raise ValueError("Amount cannot be negative")
        self.__balance += amount
        logger.info(f"Deposit successful. New balance: {self.__balance}")

    def withdraw(self, amount: float) -> None:
        if amount < 0:
            logger.error("Amount cannot be negative")
            raise ValueError("Amount cannot be negative")
        if amount > self.__balance:
            logger.error("Insufficient funds")
            raise InsufficientFundsError("Insufficient funds", amount)
        if self._account_type == "savings" and self.__balance - amount < self._min_balance():
            logger.error("Minimum balance will not be maintained after withdrawal")
            raise InsufficientFundsError(
                "Minimum balance will not be maintained after withdrawal",
                amount,
            )
        self.__balance -= amount
        logger.info(f"Withdrawal successful. New balance: {self.__balance}")

    def convert_currency(self, target_currency: str, exchange_rate: float) -> None:
        if exchange_rate <= 0:
            logger.error("Exchange rate must be positive")
            raise ValueError("Exchange rate must be positive")
        converted = self.__balance * exchange_rate
        print(f"Balance in {target_currency}: {converted}")

    @classmethod
    def create_savings(
        cls,
        account_number: str,
        currency: str = "USD",
        _account_type: str = "savings",
        balance: float = 0.0,
    ) -> "BankAccount":
        rate = cls._rates_to_usd.get(currency)
        if rate is None:
            raise ValueError(f"Unknown currency: {currency}")
        min_balance = cls._min_savings_usd / rate
        if balance < min_balance:
            logger.error("Balance cannot be less than minimum balance")
            raise ValueError("Balance cannot be less than minimum balance")
        return cls(account_number, currency, _account_type, balance)

    @staticmethod
    def is_valid_account_number(account_number: str) -> bool:
        return len(account_number) == 10 and account_number.isdigit()


class Customer:
    user_count = 0

    def __init__(self, name: str, birth_date: date):
        if not Customer.is_adult(birth_date):
            logger.error("Customer must be at least 18 years old")
            raise ValueError("Customer must be at least 18 years old")
        Customer.user_count += 1
        self._user_id = Customer.user_count
        self.name = name
        self.birth_date = birth_date
        self.__accounts: list[BankAccount] = []

    def get_user_id(self) -> int:
        return self._user_id

    def get_accounts(self) -> list[BankAccount]:
        return list(self.__accounts)

    @staticmethod
    def is_adult(birth_date: date) -> bool:
        today = date.today()
        age = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age >= 18

    def add_account(self, account: BankAccount) -> None:
        if not BankAccount.is_valid_account_number(account.get_account_number()):
            logger.error(
                f"Invalid account number; cannot add account {account.get_account_number()}"
            )
            return
        self.__accounts.append(account)
        logger.info(
            f"Account {account.get_account_number()} added to customer {self._user_id}"
        )

    def get_total_balance(self) -> float:
        total = 0.0
        for account in self.__accounts:
            total += account.get_balance()
        return total

    def transfer(
        self,
        source_account: BankAccount,
        target_account: BankAccount,
        amount: float,
    ) -> None:
        if source_account not in self.__accounts or target_account not in self.__accounts:
            logger.error("Source or target account is not held by this customer")
            return
        try:
            source_account.withdraw(amount)
            target_account.deposit(amount)
        except (InsufficientFundsError, ValueError) as error:
            logger.error(f"Transfer failed: {error}")


def menu() -> None:
    customers: list[Customer] = []

    while True:
        print("\n1. Add customer")
        print("2. Add account")
        print("3. Deposit")
        print("4. Withdraw")
        print("5. Transfer")
        print("6. Total balance")
        print("7. Convert currency")
        print("0. Exit")
        choice = input("Choice: ").strip()

        if choice == "0":
            break

        try:
            if choice == "1":
                name = input("Name: ").strip()
                birth_date = date.fromisoformat(input("Birth date (YYYY-MM-DD): ").strip())
                customer = Customer(name, birth_date)
                customers.append(customer)
                print(f"User id: {customer.get_user_id()}")

            elif choice == "2":
                user_id = int(input("Customer user id: ").strip())
                customer = None
                for c in customers:
                    if c.get_user_id() == user_id:
                        customer = c
                        break
                if customer is None:
                    print("Customer not found")
                    continue
                account_number = input("Account number (10 digits): ").strip()
                account_type = input("Account type (checking/savings): ").strip().lower()
                currency = input("Currency: ").strip().upper() or "USD"
                balance = float(input("Opening balance: ").strip())
                if account_type == "savings":
                    account = BankAccount.create_savings(account_number, currency, balance=balance)
                else:
                    account = BankAccount(account_number, currency, balance=balance)
                customer.add_account(account)

            elif choice in ("3", "4", "5", "6", "7"):
                user_id = int(input("Customer user id: ").strip())
                customer = None
                for c in customers:
                    if c.get_user_id() == user_id:
                        customer = c
                        break
                if customer is None:
                    print("Customer not found")
                    continue

                if choice == "6":
                    print(customer.get_total_balance())
                    continue

                account_number = input("Account number: ").strip()
                account = None
                for a in customer.get_accounts():
                    if a.get_account_number() == account_number:
                        account = a
                        break
                if account is None:
                    print("Account not found")
                    continue

                if choice == "3":
                    account.deposit(float(input("Amount: ").strip()))
                elif choice == "4":
                    account.withdraw(float(input("Amount: ").strip()))
                elif choice == "5":
                    target_number = input("Target account number: ").strip()
                    target = None
                    for a in customer.get_accounts():
                        if a.get_account_number() == target_number:
                            target = a
                            break
                    if target is None:
                        print("Target account not found")
                        continue
                    customer.transfer(account, target, float(input("Amount: ").strip()))
                elif choice == "7":
                    target_currency = input("Target currency: ").strip().upper()
                    exchange_rate = float(input("Exchange rate: ").strip())
                    account.convert_currency(target_currency, exchange_rate)

            else:
                print("Unknown option")

        except (ValueError, InsufficientFundsError) as error:
            print(error)


if __name__ == "__main__":
    menu()
