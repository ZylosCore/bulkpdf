import fitz
import threading
import os
from pathlib import Path

class PDFTask(threading.Thread):
    def __init__(self, files, output_path, callback_progress, callback_done, mode="merge", password=""):
        super().__init__()
        self.files = [Path(f) for f in files]
        self.output_path = str(output_path)
        self.callback_progress = callback_progress
        self.callback_done = callback_done
        self.mode = mode
        self.password = password

    def run(self):
        try:
            if self.mode == "merge": self._merge()
            elif self.mode == "compress": self._compress()
            elif self.mode == "unlock": self._unlock()
            elif self.mode == "protect": self._protect()
            elif self.mode == "extract": self._extract()
        except Exception as e:
            self.callback_done(f"Erreur: {str(e)}")

    def _protect(self):
        """Crypte un PDF même s'il est déjà protégé ou ouvert"""
        if not self.files: return
        
        # On ouvre le document source
        doc = fitz.open(str(self.files[0]))
        
        # Si le document est déjà crypté, on tente de l'ouvrir avec le MDP fourni
        if doc.is_encrypted:
            doc.authenticate(self.password)
            
        # On sauvegarde sous un nouveau nom avec le nouveau MDP
        doc.save(
            self.output_path,
            user_pw=self.password,
            encryption=fitz.PDF_ENCRYPT_AES_256,
            permissions=fitz.PDF_PERM_PRINT | fitz.PDF_PERM_COPY,
            garbage=4,
            deflate=True
        )
        doc.close()
        self.callback_done(self.output_path)

    def _unlock(self):
        doc = fitz.open(str(self.files[0]))
        if doc.is_encrypted:
            if not doc.authenticate(self.password):
                doc.close()
                raise Exception("Mot de passe incorrect pour le déverrouillage")
        doc.save(self.output_path, encryption=fitz.PDF_ENCRYPT_NONE)
        doc.close()
        self.callback_done(self.output_path)

    def _merge(self):
        doc_dest = fitz.open()
        for i, f in enumerate(self.files):
            src = fitz.open(str(f))
            if src.is_encrypted:
                src.authenticate(self.password)
            doc_dest.insert_pdf(src)
            src.close()
            self.callback_progress((i + 1) / len(self.files))
        doc_dest.save(self.output_path)
        doc_dest.close()
        self.callback_done(self.output_path)

    def _compress(self):
        doc = fitz.open(str(self.files[0]))
        doc.save(self.output_path, garbage=4, deflate=True)
        doc.close()
        self.callback_done(self.output_path)

    def _extract(self):
        output_dir = Path(self.output_path).parent / f"Images_{Path(self.output_path).stem}"
        if not output_dir.exists(): os.makedirs(output_dir)
        doc = fitz.open(str(self.files[0]))
        count = 0
        for page in doc:
            for img in page.get_images():
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha > 3: pix = fitz.Pixmap(fitz.csRGB, pix)
                pix.save(str(output_dir / f"p{page.number}_x{xref}.png"))
                count += 1
        doc.close()
        self.callback_done(f"{count} images extraites")
