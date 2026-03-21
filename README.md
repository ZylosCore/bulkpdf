# BulkPDF

**BulkPDF** is a powerful desktop application designed to manage, optimize, and secure your PDF files in bulk—quickly and securely. 

<h1 align="center">
    <br>
      <a href="#">
        <img src="./src/assets/logo.png" width="400" height="400" alt="BulkPDF logo" >
      </a>
    <br>
      BulkPDF
    <br>
</h1>

---

## Why use BulkPDF?
Working with PDFs often requires online tools that compromise the confidentiality of your data, or heavy, expensive software. 

BulkPDF is based on a **local processing engine (PyMuPDF)**: no data leaves your computer. The application is optimized for batch processing, allowing you to apply the same operation to dozens of files with a single click, with immediate visual feedback on progress and a modern “Dracula” interface powered by CustomTkinter.

---

## Detailed Features

The application is divided into several independent modules, all accessible via the sidebar.

### 1. Merge (Merge PDF)
Combine multiple documents into a single file.
* **Custom order**: Import your files and manage the merge order in the list.
* **Speed**: Instant merging even for large files.
* **Cleanup**: Option to clear the list after a successful merge.

### 2. Compression
Reduce the size of your PDF files without losing readability.
* **Smart optimization**: Reduces the size of embedded images and removes unnecessary data.
* **Batch processing**: Select an entire folder and compress it all at once.
* **Space savings indicator**: View the disk space saved after processing.

### 3. Encryption
Secure your sensitive documents with robust encryption.
* **User Password**: Restrict access to the document.
* **Owner Password**: Control permissions (printing, copying text).
* **Strong Encryption**: Uses PDF security standards for maximum protection.

### 4. Unlock
Remove restrictions from your own PDF files.
* **Password Removal**: Permanently remove the password prompt if you have the necessary permissions.
* **Batch Unlock**: Convenient for processing batches of documents protected by the same password.

### 5. Image Extraction
Extract all visual elements from your PDFs.
* **Automatic Export**: Scans the PDF and saves each image found in a dedicated folder.
* **High-Quality Formats**: Extracts images as PNG or JPG depending on the original source.

### 6. Settings
Customize your experience.
* Choose the default output folder.
* Manage the theme (Dark/Light).
* Configure compression levels.

---

## Installation

BulkPDF requires **Python 3.10 or later**.

1. **Clone the repository**:
```bash
git clone https://github.com/ZylosCore/bulkpdf
cd bulkpdf
```
Create a virtual environment:

```Bash
python -m venv venv
# Windows :
venv\Scripts\activate
# Linux/Mac :
source venv/bin/activate
```
Install the dependencies:
```Bash
pip install -r requirements.txt
```

2. How do I run the application?

Run the application from the project root directory:

```Bash
python src/main.py
```
Note: Upon launch, BulkPDF automatically generates a high-resolution system icon (.ico) from your PNG logo to ensure optimal display in the Windows taskbar.
Architecture & Security

    UI : CustomTkinter (Thème sombre natif).

    Moteur : PyMuPDF (Fitz) pour une vitesse de traitement maximale.

    Image Logic : Conversion Pillow dynamique pour adapter les icônes au mode sombre (inversion en blanc automatique).

    Confidentialité : Traitement 100% hors-ligne.

# License

This project is licensed under the MIT License. See the LICENSE file for more details.
