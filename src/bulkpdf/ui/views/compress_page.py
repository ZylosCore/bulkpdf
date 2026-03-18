from .pdf_operations import PDFOperationsView
class CompressPage(PDFOperationsView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.mode_name = "compressed"
        self.label.configure(text="optimize pdf size")
