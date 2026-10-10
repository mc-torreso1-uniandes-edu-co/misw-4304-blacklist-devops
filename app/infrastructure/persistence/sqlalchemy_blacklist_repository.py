from typing import Optional
from uuid import UUID

from sqlalchemy.orm import scoped_session

from app.application.ports.blacklist_repository import BlacklistRepository
from app.domain.blacklist_entry import BlacklistEntry
from app.infrastructure.persistence.blacklist_entry_model import BlacklistEntryModel


class SqlAlchemyBlacklistRepository(BlacklistRepository):
    def __init__(self, session: scoped_session):
        self._session = session

    def add(self, entry: BlacklistEntry) -> None:
        self._session.add(self._to_model(entry))
        self._session.commit()

    def find_by_email(self, email: str) -> Optional[BlacklistEntry]:
        model = self._session.query(BlacklistEntryModel).filter_by(email=email).first()
        return None if model is None else self._to_entity(model)

    @staticmethod
    def _to_model(entry: BlacklistEntry) -> BlacklistEntryModel:
        return BlacklistEntryModel(
            email=entry.email,
            app_uuid=str(entry.app_uuid),
            blocked_reason=entry.blocked_reason,
            ip_address=entry.ip_address,
            created_at=entry.created_at,
        )

    @staticmethod
    def _to_entity(model: BlacklistEntryModel) -> BlacklistEntry:
        return BlacklistEntry(
            email=model.email,
            app_uuid=UUID(model.app_uuid),
            blocked_reason=model.blocked_reason,
            ip_address=model.ip_address,
            created_at=model.created_at,
        )
