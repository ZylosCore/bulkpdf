import pikepdf
import threading
import sys

class PDFTask(threading.Thread):
    def __init__(self, files, output, progress_callback, done_callback, mode="merge", password=None):
        super().__init__()
        self.files = files
        self.output = output
        self.progress_callback = progress_callback
        self.done_callback = done_callback
        self.mode = mode
        self.password = str(password).strip() if password else ""
        self.daemon = True

    def run(self):
        result = None
        try:
            print(f"[*] Starting task: {self.mode} on {self.files[0] if self.files else 'No File'}")
            
            if self.mode == "unlocked":
                result = self.unlock_pdf()
            elif self.mode == "encrypted":
                result = self.protect_pdf()
            elif self.mode == "merge":
                result = self.merge_pdfs()
            elif self.mode == "compressed":
                result = self.compress_pdf()
            else:
                result = f"Error: Unknown mode {self.mode}"
        except pikepdf.PasswordError:
            result = "Error: Incorrect password"
        except Exception as e:
            result = f"Error: {str(e)}"
        finally:
            print(f"[+] Task finished with result: {result}")
            self.done_callback(result)

    def unlock_pdf(self):
        # UNLOCK : On DOIT fournir le password pour ouvrir
        with pikepdf.open(self.files[0], password=self.password) as pdf:
            pdf.save(self.output)
        return self.output

    def protect_pdf(self):
        # LOCK : On ouvre SANS password (fichier source sain)
        # On ajoute le password uniquement à la sauvegarde
        with pikepdf.open(self.files[0]) as pdf:
            enc = pikepdf.Encryption(user=self.password, owner=self.password, allow=pikepdf.Permissions(extract=False))
            pdf.save(self.output, encryption=enc)
        return self.output

    def merge_pdfs(self):
        dst = pikepdf.Pdf.new()
        for f in self.files:
            with pikepdf.open(f) as src:
                dst.pages.extend(src.pages)
        dst.save(self.output)
        return self.output

    def compress_pdf(self):
        with pikepdf.open(self.files[0]) as pdf:
            pdf.save(self.output, linearize=True)
        return self.output
