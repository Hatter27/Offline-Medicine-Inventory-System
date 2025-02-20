Medicine Inventory System - README

Version: 1.0
Developer: [Team Manifest]
Date: [2/18/2025]


---

1. Overview

The Medicine Inventory System is an offline application designed for small pharmacies. It features an Admin Panel that tracks user activities, including adding, deleting, restoring medicines, managing transactions, and discounts.

New user registrations must be approved by the admin before they can log in.

Key Features:

Medicine Encoding – Add new medicines to the inventory.

Manage Discounts – Apply Senior Citizen and PWD discounts.

View Sales – Track all transactions and sales records.

View Alerts – Receive notifications for near-expiry or low-stock medicines.

View Deleted Medicines – Track deleted medicines and restore them if needed.

View Revenue – Check total daily sales and revenue reports.

Admin Panel – Monitor user activities (who added, deleted, restored, or modified records).



---

2. System Requirements

Operating System: Windows 10/11 (64-bit)

Minimum RAM: 4GB

Storage: At least 500MB free disk space

Other Dependencies: Python and SQLite (included in the installer)



---

3. Installation Instructions

1. Extract the ZIP file (if compressed).


2. Run MedicineInventoryInstaller.exe.


3. Follow the installation steps until completion.


4. After installation, find the Medicine Inventory System shortcut on your desktop and open it.




---

4. How to Use

Login/Register – Users must create an account and wait for admin approval before logging in.

Encoding Medicines – Add new medicines to the inventory.

Managing Discounts – Apply automatic discounts for Senior Citizens and PWDs.

Tracking Sales – View all recorded transactions.

Alerts & Notifications – Monitor medicines that are low in stock or nearing expiry.

View Deleted Medicines – Check and restore deleted medicines if necessary.

Revenue Tracking – View daily total sales and revenue reports.

Admin Panel – Track which user performed actions like adding, deleting, restoring, and managing discounts.



---

5. Admin Role Management

To set an existing user as an admin, run the following SQL command in your SQLite database:

UPDATE users SET role = 'admin' WHERE username = 'admin_username';

Replace admin_username with the actual username you want to grant admin privileges to.


---

6. Database Backup

It is recommended to back up the database regularly to prevent data loss. You can manually create a backup using the following command:

sqlite3 medicine_inventory.db .dump > backup.sql

To restore the database from a backup:

sqlite3 new_medicine_inventory.db < backup.sql

Alternatively, you can automate backups using a Python script:

import shutil
import os

def backup_database():
    db_path = "medicine_inventory.db"
    backup_path = f"backup_{db_path}"

    if os.path.exists(db_path):
        shutil.copy(db_path, backup_path)
        print("Database backup successful!")
    else:
        print("Database file not found!")


---

7. Troubleshooting

If an error occurs during installation, restart the PC and try again.

If the application does not open, try running it as Administrator.

Check the logs/ folder for any error messages if the system is not functioning correctly.



---

8. Developer Contact

For any issues or suggestions, you may contact the developer: 📧 Email: [nikoabella13@gmail.com]
📞 Contact Number: [09504056580]
