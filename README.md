# XML Error Corrector System

A Django-based web application developed for the **Cooperative Bank of Tanzania** to simplify the correction of XML error files returned from the **Bank of Tanzania (BoT)**.

## 🚀 Project Overview

When businesses submit payment batch files to the Bank of Tanzania, they sometimes receive XML reports containing credential errors (e.g. incorrect National ID, Account Number, or Amount). This system enables business users—especially those without a technical background—to upload those XML files, view and understand the errors, and correct them easily through a user-friendly dashboard.

## 🧩 Features

- ✅ **XML File Upload**
- 🗃️ **Batch History** for tracking uploads
- 📄 **Error Parsing** from `<Command>` blocks and `<parameter>` tags
- 🧑‍💼 **Card-Based UI** to display each customer error individually
- ✏️ **Strikethrough Error Highlighting** for easy recognition
- 🔐 **User Authentication** (Sign Up, Login, Logout)
- 📊 **Simple Dashboard Interface** tailored for non-technical users

## 🛠️ Technologies Used

- **Python 3.x**
- **Django**
- **HTML/CSS/JavaScript**
- **Bootstrap** or **TailwindCSS** (optional based on your UI design)
- **SQLite / PostgreSQL** (configurable)

## 🧮 How It Works

1. User uploads an XML error file from BoT.
2. The system parses each `<Command>` block and extracts:
   - Customer details
   - The cause of the error (from `<Exception>` and its `<parameter>` tags)
3. All data is saved in the database and displayed in an error dashboard.
4. Users can review, correct, and export the clean version.

## 📂 Folder Structure (Sample)

