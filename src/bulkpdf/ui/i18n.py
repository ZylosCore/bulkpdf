import os
import json
from pathlib import Path

TRANSLATIONS = {
    "en": {
        "app_title": "BulkPDF - Professional PDF Suite",
        "menu_merge": "Merge",
        "menu_extract": "Split & Extract",
        "menu_edit": "PDF Editor",
        "menu_compress": "Compress",
        "menu_protect": "Protect",
        "menu_unlock": "Unlock",
        "menu_settings": "Settings",
        
        "btn_open": "Open",
        "btn_save": "Save",
        "btn_rotate": "Rotate",
        "btn_enlarge": "Enlarge",
        "btn_shrink": "Shrink",
        "btn_delete": "Delete",
        "btn_add_pdf": "+ Add PDFs",
        "btn_clear_list": "Clear List",
        "btn_merge_save": "Merge & Save",
        "btn_extract_save": "Extract & Save",
        "btn_choose_pdf": "Choose a PDF file",
        
        "settings_title": "Settings",
        "lang_lbl": "Application Language",
        "restart_msg": "Please restart the application to apply the new language.",
        
        "page_lbl": "Page",
        "success": "Success",
        "error": "Error",
        "warning": "Warning",
        "doc_saved": "Document saved successfully!",
        "sig_not_found": "Signature file not found.",
        "load_sig": "Load Signature (PNG)",
        
        "merge_title": "Merge PDFs",
        "no_file_selected": "No file selected.\nClick on 'Add PDFs'.",
        "merge_min_files": "Please select at least 2 PDF files to merge.",
        "merge_success": "PDFs have been merged successfully!",
        
        "extract_title": "Split & Extract",
        "extract_no_file": "No file selected",
        "extract_ready": "Document ready. Contains {} page(s).",
        "extract_from": "Extract from page:",
        "extract_to": "to page:",
        "extract_format": "Output format:",
        "format_pdf": "Single PDF containing the selection",
        "format_zip": "ZIP Archive (1 PDF file per page)",
        "extract_err_num": "Please enter valid page numbers (digits only).",
        "extract_err_range": "Invalid range. Pages must be between 1 and {}.",
        "extract_success_pdf": "The PDF has been generated successfully!",
        "extract_success_zip": "The ZIP archive was created successfully!"
    },
    "fr": {
        "app_title": "BulkPDF - Suite PDF Professionnelle",
        "menu_merge": "Fusionner",
        "menu_extract": "Séparer",
        "menu_edit": "Éditeur PDF",
        "menu_compress": "Compresser",
        "menu_protect": "Protéger",
        "menu_unlock": "Déverrouiller",
        "menu_settings": "Paramètres",
        
        "btn_open": "Ouvrir",
        "btn_save": "Enregistrer",
        "btn_rotate": "Rotation",
        "btn_enlarge": "Agrandir",
        "btn_shrink": "Réduire",
        "btn_delete": "Supprimer",
        "btn_add_pdf": "+ Ajouter des PDF",
        "btn_clear_list": "Vider la liste",
        "btn_merge_save": "Fusionner et Sauvegarder",
        "btn_extract_save": "Extraire et Sauvegarder",
        "btn_choose_pdf": "Choisir un fichier PDF",
        
        "settings_title": "Paramètres",
        "lang_lbl": "Langue de l'application",
        "restart_msg": "Veuillez redémarrer l'application pour appliquer la langue.",
        
        "page_lbl": "Page",
        "success": "Succès",
        "error": "Erreur",
        "warning": "Attention",
        "doc_saved": "Document enregistré avec succès !",
        "sig_not_found": "Fichier de signature introuvable.",
        "load_sig": "Charger une signature (PNG)",
        
        "merge_title": "Fusionner des PDF",
        "no_file_selected": "Aucun fichier sélectionné.\nCliquez sur 'Ajouter des PDF'.",
        "merge_min_files": "Veuillez sélectionner au moins 2 fichiers PDF à fusionner.",
        "merge_success": "Les PDF ont été fusionnés avec succès !",
        
        "extract_title": "Séparer & Extraire",
        "extract_no_file": "Aucun fichier sélectionné",
        "extract_ready": "Document prêt. Contient {} page(s).",
        "extract_from": "Extraire de la page :",
        "extract_to": "à la page :",
        "extract_format": "Format de sortie :",
        "format_pdf": "Un seul PDF contenant la sélection",
        "format_zip": "Archive ZIP (1 fichier PDF par page)",
        "extract_err_num": "Veuillez entrer des numéros de page valides (chiffres).",
        "extract_err_range": "Plage invalide. Les pages doivent être entre 1 et {}.",
        "extract_success_pdf": "Le PDF a été généré avec succès !",
        "extract_success_zip": "L'archive ZIP a été créée avec succès !"
    },
    "ar": {
        "app_title": "BulkPDF - حزمة PDF الاحترافية",
        "menu_merge": "دمج",
        "menu_extract": "تقسيم واستخراج",
        "menu_edit": "محرر PDF",
        "menu_compress": "ضغط",
        "menu_protect": "حماية",
        "menu_unlock": "إلغاء القفل",
        "menu_settings": "الإعدادات",
        
        "btn_open": "فتح",
        "btn_save": "حفظ",
        "btn_rotate": "تدوير",
        "btn_enlarge": "تكبير",
        "btn_shrink": "تصغير",
        "btn_delete": "حذف",
        "btn_add_pdf": "+ إضافة ملفات PDF",
        "btn_clear_list": "مسح القائمة",
        "btn_merge_save": "دمج وحفظ",
        "btn_extract_save": "استخراج وحفظ",
        "btn_choose_pdf": "اختر ملف PDF",
        
        "settings_title": "الإعدادات",
        "lang_lbl": "لغة التطبيق",
        "restart_msg": "يرجى إعادة تشغيل التطبيق لتطبيق تغييرات اللغة.",
        
        "page_lbl": "صفحة",
        "success": "نجاح",
        "error": "خطأ",
        "warning": "تحذير",
        "doc_saved": "تم حفظ المستند بنجاح!",
        "sig_not_found": "لم يتم العثور على ملف التوقيع.",
        "load_sig": "تحميل التوقيع (PNG)",
        
        "merge_title": "دمج ملفات PDF",
        "no_file_selected": "لم يتم تحديد أي ملف.\nانقر على 'إضافة ملفات PDF'.",
        "merge_min_files": "يرجى تحديد ملفين PDF على الأقل للدمج.",
        "merge_success": "تم دمج ملفات PDF بنجاح!",
        
        "extract_title": "تقسيم واستخراج",
        "extract_no_file": "لم يتم تحديد أي ملف",
        "extract_ready": "المستند جاهز. يحتوي على {} صفحة/صفحات.",
        "extract_from": "استخراج من الصفحة:",
        "extract_to": "إلى الصفحة:",
        "extract_format": "تنسيق الإخراج:",
        "format_pdf": "ملف PDF واحد يحتوي على التحديد",
        "format_zip": "أرشيف ZIP (ملف PDF واحد لكل صفحة)",
        "extract_err_num": "يرجى إدخال أرقام صفحات صالحة (أرقام فقط).",
        "extract_err_range": "نطاق غير صالح. يجب أن تكون الصفحات بين 1 و {}.",
        "extract_success_pdf": "تم إنشاء ملف PDF بنجاح!",
        "extract_success_zip": "تم إنشاء أرشيف ZIP بنجاح!"
    }
}

class LanguageManager:
    def __init__(self):
        self.config_file = Path(os.getenv('APPDATA', '.')) / "BulkPDF" / "config.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.current_lang = self.load_language()

    def load_language(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    return config.get("language", "en")
            except: pass
        return "en"

    def set_language(self, lang):
        if lang in TRANSLATIONS:
            self.current_lang = lang
            config = {}
            if self.config_file.exists():
                try:
                    with open(self.config_file, "r", encoding="utf-8") as f:
                        config = json.load(f)
                except: pass
            config["language"] = lang
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f)

    def translate(self, key):
        return TRANSLATIONS.get(self.current_lang, TRANSLATIONS["en"]).get(key, key)

i18n = LanguageManager()

def t(key):
    return i18n.translate(key)