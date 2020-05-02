import datetime as dt
from typing import ClassVar, Optional

from clabe import Clabe
from pydantic import BaseModel, StrictStr
from pydantic.dataclasses import dataclass

from ..types import Network, Status, StrictPositiveInt
from .base import Creatable, Listable, Retrievable


class TransferRequest(BaseModel):
    account_number: Clabe
    amount: StrictPositiveInt  # in centavos
    descriptor: StrictStr  # how it'll appear for the recipient
    idempotency_key: str  # must be unique for each transfer


@dataclass
class Transfer(Creatable, Listable, Retrievable):
    _endpoint: ClassVar = '/transfers'
    _query_params: ClassVar = {'account_number', 'idempotency_key', 'status'}

    id: str
    created_at: dt.datetime
    updated_at: dt.datetime
    account_number: str
    amount: int  # in centavos
    descriptor: str  # how it'll appear for the recipient
    idempotency_key: str
    status: Status
    network: Network
    tracking_key: Optional[str] = None  # clave rastreo

    @classmethod
    def create(
        cls,
        account_number: str,
        amount: int,
        descriptor: str,
        idempotency_key: Optional[str] = None,
    ) -> 'Transfer':
        """
        - amount: needs to be in centavos (not pesos)
        - descriptor: how it'll appear for the recipient
        - idempotency_key: must be unique for each transfer to avoid duplicates

        The recommended idempotency_key scheme:
        1. create a transfer entry in your own database with the status
            created
        2. call this method with the unique id from your database as the
            idempotency_key
        3. update your database with the status pending or submitted after
            receiving a response from this method
        """
        if not idempotency_key:
            idempotency_key = cls._gen_idempotency_key(account_number, amount)
        req = TransferRequest(
            account_number=account_number,
            amount=amount,
            descriptor=descriptor,
            idempotency_key=idempotency_key,
        )
        return super().create(req.dict())

    @staticmethod
    def _gen_idempotency_key(account_number: str, amount: int) -> str:
        """
        We *strongly* recommend using your own internal database id as the
        idempotency_key, but this provides some level of protection against
        submitting duplicate transfers
        """
        return f'{dt.datetime.utcnow().date()}:{account_number}:{amount}'
