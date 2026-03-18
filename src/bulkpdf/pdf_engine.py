import pikepdf
import threading

class PDFTask(threading.Thread):
    def __init__(self, files, output, progress_callback, done_callback, mode="merge", password=None):
        super().__init__()
        self.files = files
        self.output = output
        self.progress_callback = progress_callback
        self.done_callback = done_callback
        self.mode = mode
        # On garde le mot de passe brut pour les tests d'encodage
        self.password_raw = str(password).strip() if password else ""
        self.daemon = True

    def run(self):
        result = None
        try:
            if self.mode == "unlocked": result = self.unlock_pdf()
            elif self.mode == "encrypted": result = self.protect_pdf()
            elif self.mode == "merge": result = self.merge_pdfs()
            elif self.mode == "compressed": result = self.compress_pdf()
        except Exception as e:
            err = str(e).lower()
            if "password" in err or "unauthenticated" in err:
                result = "Error: Incorrect password"
            else:
                result = f"Error: {str(e)}"
        finally:
            self.done_callback(result)

    def unlock_pdf(self):
        # TENTATIVE 1 : Mot de passe normal
        try:
            with pikepdf.open(self.files[0], password=self.password_raw) as pdf:
                pdf.save(self.output)
                return self.output
        except pikepdf.PasswordError:
            # TENTATIVE 2 : On essaie avec un encodage différent (pour les caractères spéciaux)
            try:
                alt_pass = self.password_raw.encode('utf-8').decode('latin-1')
                with pikepdf.open(self.files[0], password=alt_pass) as pdf:
                    pdf.save(self.output)
                    return self.output
            except:
                raise pikepdf.PasswordError("Incorrect password")

    def protect_pdf(self):
        with pikepdf.open(self.files[0]) as pdf:
            enc = pikepdf.Encryption(user=self.password_raw, owner=self.password_raw, R=6)
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
