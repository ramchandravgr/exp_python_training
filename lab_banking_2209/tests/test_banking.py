from datetime import date

import pytest

from src.banking import BankAccount, Customer, InsufficientFundsError


# --- BankAccount ---


def test_getters():
    account = BankAccount("1234567890", currency="USD", balance=50)
    assert account.get_account_number() == "1234567890"
    assert account.get_currency() == "USD"
    assert account.get_account_type() == "checking"
    assert account.get_balance() == 50


def test_set_balance_ok():
    account = BankAccount("1234567890", balance=10)
    account.set_balance(25)
    assert account.get_balance() == 25


def test_set_balance_negative_raises():
    account = BankAccount("1234567890", balance=10)
    with pytest.raises(ValueError):
        account.set_balance(-1)


def test_deposit():
    account = BankAccount("1234567890", balance=10)
    account.deposit(5)
    assert account.get_balance() == 15


def test_deposit_negative_raises():
    account = BankAccount("1234567890", balance=10)
    with pytest.raises(ValueError):
        account.deposit(-5)


def test_withdraw():
    account = BankAccount("1234567890", balance=20)
    account.withdraw(8)
    assert account.get_balance() == 12


def test_withdraw_negative_raises():
    account = BankAccount("1234567890", balance=20)
    with pytest.raises(ValueError):
        account.withdraw(-1)


def test_withdraw_insufficient_funds():
    account = BankAccount("1234567890", balance=10)
    with pytest.raises(InsufficientFundsError) as error:
        account.withdraw(50)
    assert error.value.amount == 50


def test_savings_withdraw_keeps_minimum():
    account = BankAccount.create_savings("1234567890", balance=150)
    with pytest.raises(InsufficientFundsError):
        account.withdraw(60)  # would go below $100


def test_convert_currency(capsys):
    account = BankAccount("1234567890", balance=100)
    account.convert_currency("EUR", 0.9)
    printed = capsys.readouterr().out
    assert "EUR" in printed
    assert "90" in printed


def test_convert_currency_bad_rate():
    account = BankAccount("1234567890", balance=100)
    with pytest.raises(ValueError):
        account.convert_currency("EUR", 0)
    with pytest.raises(ValueError):
        account.convert_currency("EUR", -2)


def test_create_savings_ok():
    account = BankAccount.create_savings("1234567890", balance=100)
    assert account.get_account_type() == "savings"
    assert account.get_balance() == 100


def test_create_savings_too_low():
    with pytest.raises(ValueError):
        BankAccount.create_savings("1234567890", balance=50)


def test_is_valid_account_number():
    assert BankAccount.is_valid_account_number("1234567890") is True
    assert BankAccount.is_valid_account_number("123") is False
    assert BankAccount.is_valid_account_number("123456789a") is False


# --- Customer ---


def test_customer_must_be_adult():
    Customer.user_count = 0
    with pytest.raises(ValueError):
        Customer("Kid", date(2020, 1, 1))


def test_customer_adult_gets_user_id():
    Customer.user_count = 0
    customer = Customer("Ada", date(1990, 5, 1))
    assert customer.get_user_id() == 1
    assert Customer.is_adult(date(1990, 5, 1)) is True


def test_add_account_valid():
    Customer.user_count = 0
    customer = Customer("Ada", date(1990, 5, 1))
    account = BankAccount("1234567890", balance=40)
    customer.add_account(account)
    assert len(customer.get_accounts()) == 1


def test_add_account_invalid_number_is_ignored():
    Customer.user_count = 0
    customer = Customer("Ada", date(1990, 5, 1))
    account = BankAccount("123", balance=40)  # invalid length, but object can still exist
    # is_valid_account_number checks the number string; constructor does not block short numbers
    customer.add_account(account)
    assert len(customer.get_accounts()) == 0


def test_get_total_balance():
    Customer.user_count = 0
    customer = Customer("Ada", date(1990, 5, 1))
    customer.add_account(BankAccount("1234567890", balance=10))
    customer.add_account(BankAccount("1234567891", balance=15))
    assert customer.get_total_balance() == 25


def test_transfer():
    Customer.user_count = 0
    customer = Customer("Ada", date(1990, 5, 1))
    source = BankAccount("1234567890", balance=50)
    target = BankAccount("1234567891", balance=10)
    customer.add_account(source)
    customer.add_account(target)

    customer.transfer(source, target, 20)

    assert source.get_balance() == 30
    assert target.get_balance() == 30
