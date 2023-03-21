from datetime import date

from sqlalchemy import (
    create_engine,
    String,
    Column,
    Date,
    Numeric,
    ForeignKey,
    UniqueConstraint,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import uuid

from .schemas import AccountSchema, EntrySchema, UserSchema

base = declarative_base()


class UserModel(base):
    __tablename__ = "app_user"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True)
    password = Column(String)
    salt = Column(String)
    name = Column(String)
    created = Column(Date)


class AccountModel(base):
    __tablename__ = "account"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app_user.id"))
    name = Column(String)
    description = Column(String)
    type = Column(String)
    credit_entries = relationship(
        "EntryModel", primaryjoin="EntryModel.credit_account_id == AccountModel.id"
    )
    debit_entries = relationship(
        "EntryModel", primaryjoin="EntryModel.debit_account_id == AccountModel.id"
    )
    __table_args__ = (UniqueConstraint("name", "user_id", "type"),)


class EntryTagModel(base):
    """Association table for entry tags"""

    __tablename__ = "entry_tag"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app_user.id"))
    entry_id = Column(UUID(as_uuid=True), ForeignKey("entry.id"))
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tag.id"))
    entry = relationship("EntryModel", back_populates="tags")
    tag = relationship("TagModel", back_populates="entries")


class TagModel(base):
    __tablename__ = "tag"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app_user.id"))
    tag = Column(String)
    entries = relationship("EntryTagModel", back_populates="tag")


class EntryModel(base):
    __tablename__ = "entry"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("app_user.id"))
    who = Column(String)
    when = Column(Date)
    credit_account_id = Column(UUID(as_uuid=True), ForeignKey(AccountModel.id))
    credit_account = relationship(
        "AccountModel",
        back_populates="credit_entries",
        foreign_keys=[credit_account_id],
    )
    debit_account_id = Column(UUID(as_uuid=True), ForeignKey(AccountModel.id))
    debit_account = relationship(
        "AccountModel", back_populates="debit_entries", foreign_keys=[debit_account_id]
    )
    amount = Column(Numeric)
    description = Column(String)
    tags = relationship("EntryTagModel", back_populates="entry")
    template = Column(Boolean)


class Database:
    def __init__(self, db_string):
        self.db = create_engine(db_string, echo=True)
        base.metadata.create_all(self.db)
        self.current_uid = None

    def set_current_user(self, email: str):
        with sessionmaker(self.db).begin() as session:
            user = session.query(UserModel).filter_by(email=email).first()
            self.current_uid = user.id

    def create_account(self, account):
        with sessionmaker(self.db).begin() as session:
            acc = AccountModel(
                user_id=self.current_uid,
                name=account["name"],
                description=account["description"],
                type=account["type"],
            )
            try:
                session.add(acc)
                session.commit()
                return True
            except IntegrityError:
                return False

    def create_user(self, user):
        with sessionmaker(self.db).begin() as session:
            user_m = UserModel(
                name=user["name"],
                email=user["email"],
                password=user["password"],
                salt=user["salt"],
                created=user["created"],
            )
            try:
                session.add(user_m)
                session.commit()
                return True
            except IntegrityError:
                return False

    def get_user(self, email):
        with sessionmaker(self.db).begin() as session:
            user = session.query(UserModel).filter_by(email=email).first()

            if not user:
                return None

            return UserSchema().load(
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "password": user.password,
                    "salt": user.salt,
                    "created": user.created.isoformat(),
                }
            )

    def add_entry(self, entry):
        with sessionmaker(self.db).begin() as session:
            entry_m = EntryModel(
                user_id=self.current_uid,
                who=entry["who"],
                when=entry["when"],
                amount=entry["amount"],
                description=entry["description"],
            )
            debit_account = (
                session.query(AccountModel)
                .filter_by(name=entry["debit_account"])
                .first()
            )
            credit_account = (
                session.query(AccountModel)
                .filter_by(name=entry["credit_account"])
                .first()
            )
            if not credit_account or not debit_account:
                return False

            entry_m.credit_account = credit_account
            entry_m.debit_account = debit_account

            if entry.get("tags", None):
                for tag_name in entry["tags"]:
                    entry_tag = EntryTagModel(user_id=self.current_uid)
                    entry_tag.tag = (
                        session.query(TagModel).filter(TagModel.tag == tag_name).first()
                    )
                    if not entry_tag.tag:
                        entry_tag.tag = TagModel(user_id=self.current_uid, tag=tag_name)

                    entry_m.tags.append(entry_tag)

            session.add(entry_m)
            return True

    def delete_entry(self, entry_id):
        with sessionmaker(self.db).begin() as session:
            entry = (
                session.query(EntryModel)
                .filter_by(user_id=self.current_uid, id=entry_id)
                .first()
            )
            if not entry:
                return False

            # TODO: this could be improved with cascade
            for entry_tag in entry.tags:
                session.delete(entry_tag)
            session.delete(entry)
            return True

    def list_entries(self, **kwargs):
        """
        List entries from database
        To filter the entries use following keyword arguments
            - debit_account=<string> - show entries debiting this account
            - credit_account=<string> - show entries crediting this account
            - from=<yyyy-mm-dd> - show entries from this date
            - to=<yyyy-mm-dd> - show entries to this date
        """
        dr = kwargs.get("debit_account", None)
        cr = kwargs.get("credit_account", None)
        _from = kwargs.get("from", None)
        to = kwargs.get("to", None)

        with sessionmaker(self.db).begin() as session:
            entries = session.query(EntryModel).filter_by(user_id=self.current_uid)
            if dr:
                entries = entries.filter(EntryModel.debit_account.has(name=dr))
            if cr:
                entries = entries.filter(EntryModel.credit_account.has(name=cr))
            if _from:
                _from = date.fromisoformat(_from)
                entries = entries.filter(EntryModel.when >= _from)
            if to:
                to = date.fromisoformat(to)
                entries = entries.filter(EntryModel.when <= to)

            entry_list = []
            for entry in entries:
                entry_list.append(
                    EntrySchema().load(
                        {
                            "id": entry.id,
                            "when": str(entry.when),
                            "description": entry.description,
                            "credit_account": entry.credit_account.name,
                            "debit_account": entry.debit_account.name,
                            "amount": entry.amount,
                            "who": entry.who,
                            # entry.tags are EntryTag associations
                            # Maybe association_proxy could be used?
                            "tags": [entry_tag.tag.tag for entry_tag in entry.tags],
                        }
                    )
                )
            return entry_list

    def list_accounts(self, **kwargs):
        """
        List accounts from database
        To filter the accounts use following keyword arguments
            - type [string] - show accounts of that type
            - name [string] - show accounts with specific name
        """
        type_ = kwargs.get("type", None)
        name = kwargs.get("name", None)
        filter_by = {}
        if type_:
            filter_by["type"] = type_
        if name:
            filter_by["name"] = name

        with sessionmaker(self.db).begin() as session:
            accounts = session.query(AccountModel).filter_by(
                user_id=self.current_uid, **filter_by
            )

            acc_list = []
            for account in accounts:
                acc_list.append(
                    AccountSchema().load(
                        {
                            "id": account.id,
                            "name": account.name,
                            "description": account.description,
                            "type": account.type,
                        }
                    )
                )
            return acc_list
