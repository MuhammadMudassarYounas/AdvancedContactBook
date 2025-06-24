import os
import json
import csv
import pickle
import logging
from datetime import datetime
from cryptography.fernet import Fernet
from typing import List, Dict

# Configure logging
logging.basicConfig(
    filename='contact_system.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ------------------ Contact Model ------------------ #
class AdvancedContact:
    def __init__(self, name: str, phone: str, email: str = "", address: str = "", category: str = "General"):
        self.name = name
        self.phone = phone
        self.email = email
        self.address = address
        self.category = category
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def __str__(self):
        return (
            f"Name: {self.name}\nPhone: {self.phone}\nEmail: {self.email}\n"
            f"Address: {self.address}\nCategory: {self.category}\n"
            f"Created: {self.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Last Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')}"
        )

    def to_dict(self):
        return {
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'category': self.category,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

# ------------------ Secure File Handler ------------------ #
class SecureFileHandler:
    def __init__(self, key_file='encryption.key'):
        self.key_file = key_file
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)

    def _load_or_generate_key(self) -> bytes:
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key

    def encrypt_data(self, data: str) -> bytes:
        return self.cipher.encrypt(data.encode())

    def decrypt_data(self, encrypted_data: bytes) -> str:
        return self.cipher.decrypt(encrypted_data).decode()

    def save_to_encrypted_json(self, data: List[Dict], file_path: str) -> None:
        encrypted = self.encrypt_data(json.dumps(data))
        with open(file_path, 'wb') as f:
            f.write(encrypted)

    def load_from_encrypted_json(self, file_path: str) -> List[Dict]:
        try:
            with open(file_path, 'rb') as f:
                decrypted = self.decrypt_data(f.read())
            return json.loads(decrypted)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

# ------------------ Contact Book Logic ------------------ #
class AdvancedContactBook:
    def __init__(self):
        self.contacts: List[AdvancedContact] = []
        self.file_handler = SecureFileHandler()
        self.storage_file = 'contacts.encrypted'
        self.backup_dir = 'backups'
        os.makedirs(self.backup_dir, exist_ok=True)
        self.load_contacts()

    def add_contact(self, contact: AdvancedContact):
        self.contacts.append(contact)
        self.save_contacts()
        logging.info(f"Added contact: {contact.name}")
        print(f"\n✅ Contact '{contact.name}' added successfully!")

    def view_contacts(self):
        if not self.contacts:
            print("📭 No contacts available.")
        for contact in self.contacts:
            print(contact)
            print("-" * 40)

    def search_contacts(self, **kwargs) -> List[AdvancedContact]:
        results = []
        for contact in self.contacts:
            if all(getattr(contact, k, '').lower().find(v.lower()) != -1 for k, v in kwargs.items()):
                results.append(contact)
        return results

    def update_contact(self, name: str, **kwargs) -> bool:
        for contact in self.contacts:
            if contact.name.lower() == name.lower():
                contact.update(**kwargs)
                self.save_contacts()
                logging.info(f"Updated contact: {contact.name}")
                return True
        return False

    def delete_contact(self, name: str) -> bool:
        for i, contact in enumerate(self.contacts):
            if contact.name.lower() == name.lower():
                del self.contacts[i]
                self.save_contacts()
                logging.info(f"Deleted contact: {contact.name}")
                return True
        return False

    def save_contacts(self):
        data = [c.to_dict() for c in self.contacts]
        self.file_handler.save_to_encrypted_json(data, self.storage_file)

    def load_contacts(self):
        data = self.file_handler.load_from_encrypted_json(self.storage_file)
        for item in data:
            item['created_at'] = datetime.fromisoformat(item['created_at'])
            item['updated_at'] = datetime.fromisoformat(item['updated_at'])
            self.contacts.append(AdvancedContact(**item))

# ------------------ CLI Interface ------------------ #
if __name__ == "__main__":
    book = AdvancedContactBook()

    while True:
        print("\n===== Contact Book Menu =====")
        print("1. Add Contact")
        print("2. View All Contacts")
        print("3. Search Contact")
        print("4. Update Contact")
        print("5. Delete Contact")
        print("0. Exit")

        choice = input("Enter choice: ")

        if choice == "1":
            name = input("Name: ")
            phone = input("Phone: ")
            email = input("Email: ")
            address = input("Address: ")
            category = input("Category: ")
            book.add_contact(AdvancedContact(name, phone, email, address, category))

        elif choice == "2":
            book.view_contacts()

        elif choice == "3":
            field = input("Search by (name/phone/email/category): ")
            value = input("Enter value to search: ")
            results = book.search_contacts(**{field: value})
            if results:
                for r in results:
                    print(r)
                    print("-" * 40)
            else:
                print("❌ No matching contact found.")

        elif choice == "4":
            name = input("Enter contact name to update: ")
            field = input("Field to update (phone/email/address/category): ")
            new_value = input("New value: ")
            success = book.update_contact(name, **{field: new_value})
            print("✅ Contact updated." if success else "❌ Contact not found.")

        elif choice == "5":
            name = input("Enter name to delete: ")
            success = book.delete_contact(name)
            print("🗑️ Deleted." if success else "❌ Contact not found.")

        elif choice == "0":
            print("👋 Exiting. Bye!")
            break

        else:
            print("❌ Invalid choice. Try again.")
