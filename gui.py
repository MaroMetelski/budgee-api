from budgee.json_storage import JsonStorage

import customtkinter

customtkinter.set_appearance_mode("System")

class EntriesFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.entry_frames = []

    def set_entries(self, entries):
        for frame in self.entry_frames:
            frame.destroy()

        self.entry_frames.clear()

        for i, _ in enumerate(entries):
            self.entry_frames.append(EntryFrame(self, "%d entry" % i))
            self.grid_rowconfigure(i, weight=1)
            self.entry_frames[i].grid(row=i, column=0, padx=10, pady=10, sticky="ew")


class EntryFrame(customtkinter.CTkFrame):
    def __init__(self, master, text, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.text = customtkinter.CTkLabel(self, text=text)
        self.text.grid(row=0, column=0, padx=10, pady=10, sticky="ew")


class AddEntryView(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws / 2) - (400 / 2)
        y = (hs / 2) - (300 / 2)

        self.geometry("400x300+%d+%d" % (x, y))


class AppView(customtkinter.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws / 2) - (500 / 2)
        y = (hs / 2) - (400 / 2)

        self.geometry("500x400+%d+%d" % (x, y))

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Data backend for storage
        self.storage = None

        # Data state
        self.entries = []

        self.entries_frame = EntriesFrame(master=self)
        self.entries_frame.grid(row=0, column=0, sticky="nsew")

    def set_storage(self, storage):
        self.storage = storage

    def load_entries(self):
        self.entries = self.storage.list_entries()
        self.entries_frame.set_entries(self.entries)

# test_entry = EntrySchema().load(
#     {
#         "id": "12345678-1234-1234-1234-123456789abc",
#         "when": "2024-02-01",
#         "credit_account": "Cash",
#         "debit_account": "Wydatek",
#         "amount": "69.0",
#         "tags": ["tag1", "tag2"],
#         "description": "Zielono mi",
#     }
# )

# test_entry = EntrySchema().dump(test_entry)

storage = JsonStorage("store.json")

app = AppView()
app.set_storage(storage)
app.load_entries()
app.mainloop()
