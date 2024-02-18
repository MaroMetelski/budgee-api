import json
import os

from .storage import Storage


class JsonStorage():
    INDENT_LEVEL = 3

    def __init__(self, file):
        self._file = file
        self._transactions = {"transactions": []}

        if not os.path.isfile(self._file):
            self._store_transactions(self._transactions)

        self._load_transactions()

    def _load_transactions(self):
        with open(self._file, 'r+', newline='') as f:
            self._transactions = json.load(f)

    def _store_transactions(self, transactions):
        with open(self._file, 'w+', newline='') as f:
            json.dump(transactions, f, indent=self.INDENT_LEVEL)

    def add_entry(self, entry):
        self._transactions["transactions"].append(entry)
        self._store_transactions(self._transactions)

    def list_entries(self, **kwargs):
        self._load_transactions()
        return self._transactions["transactions"]
