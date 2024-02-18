from abc import ABC, abstractmethod

class Storage(ABC):
    """Abstract class for application data storage interface."""

    @abstractmethod
    def create_user(self, user):
        pass

    @abstractmethod
    def get_user(self, email):
        pass

    @abstractmethod
    def delete_entry(self, entry):
        pass

    @abstractmethod
    def list_entries(self, **kwargs):
        pass

    @abstractmethod
    def add_entry(self, entry):
        pass

    @abstractmethod
    def create_account(self, account):
        pass

    @abstractmethod
    def delete_entry(self, entry_id):
        pass

    @abstractmethod
    def list_accounts(self, **kwargs):
        pass
