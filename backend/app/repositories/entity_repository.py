"""FraudDNA Entity Repository.

Provides persistent access for core financial entities:
Customer, Account, Card, Device, IPAddress, Merchant, and RiskNetwork.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import (
    AccountModel,
    CardModel,
    CustomerModel,
    DeviceModel,
    IPAddressModel,
    MerchantModel,
    RiskNetworkModel,
)


class EntityRepository:
    """Encapsulates entity queries across relational tables."""

    def get_customer(self, session: Session, customer_id: str) -> CustomerModel | None:
        """Retrieve customer entity by ID."""
        stmt = select(CustomerModel).where(CustomerModel.id == customer_id)
        return session.execute(stmt).scalar_one_or_none()

    def get_account(self, session: Session, account_id: str) -> AccountModel | None:
        """Retrieve account entity by ID."""
        stmt = select(AccountModel).where(AccountModel.id == account_id)
        return session.execute(stmt).scalar_one_or_none()

    def get_card(self, session: Session, card_id: str) -> CardModel | None:
        """Retrieve card payment instrument by ID."""
        stmt = select(CardModel).where(CardModel.id == card_id)
        return session.execute(stmt).scalar_one_or_none()

    def get_device(self, session: Session, device_id: str) -> DeviceModel | None:
        """Retrieve device entity by ID."""
        stmt = select(DeviceModel).where(DeviceModel.id == device_id)
        return session.execute(stmt).scalar_one_or_none()

    def get_ip_address(self, session: Session, ip_address: str) -> IPAddressModel | None:
        """Retrieve IP address entity by ID."""
        stmt = select(IPAddressModel).where(IPAddressModel.id == ip_address)
        return session.execute(stmt).scalar_one_or_none()

    def get_merchant(self, session: Session, merchant_id: str) -> MerchantModel | None:
        """Retrieve merchant entity by ID."""
        stmt = select(MerchantModel).where(MerchantModel.id == merchant_id)
        return session.execute(stmt).scalar_one_or_none()

    def get_risk_network(self, session: Session, network_id: str) -> RiskNetworkModel | None:
        """Retrieve risk network entity by ID."""
        stmt = select(RiskNetworkModel).where(RiskNetworkModel.id == network_id)
        return session.execute(stmt).scalar_one_or_none()
