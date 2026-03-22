# Neo-Productivity Theme (Inspired by modern 2024 UI trends like Vercel/Linear)
# High contrast, clean, and motivating for productivity tools.

# --- COLORS ---
# Backgrounds (Soft Zinc for Light mode, Very Dark Zinc for Dark mode)
BG_COLOR = ("#F4F4F5", "#09090B")          
SIDEBAR_COLOR = ("#FFFFFF", "#18181B")     
TOPBAR_COLOR = ("#FFFFFF", "#18181B")      
CARD_COLOR = ("#FFFFFF", "#18181B")        
BORDER_COLOR = ("#E4E4E7", "#27272A")      

# Accents (Vibrant Indigo - highly professional and motivating)
ACCENT_PRIMARY = ("#4F46E5", "#6366F1")    
ACCENT_PRIMARY_HOVER = ("#4338CA", "#4F46E5") 

# MODIF: Darker, deeper green for excellent contrast with white text
ACCENT_SUCCESS = ("#15803D", "#22C55E")    # Green 700 / Green 500
ACCENT_SUCCESS_HOVER = ("#166534", "#16A34A")

ACCENT_DANGER = ("#EF4444", "#F87171")     # Rose/Red
ACCENT_DANGER_HOVER = ("#DC2626", "#EF4444")

# Text Colors
TEXT_MAIN = ("#18181B", "#F4F4F5")        
TEXT_TITLE = ("#09090B", "#FFFFFF")       
TEXT_LOW = ("#71717A", "#A1A1AA")         

# Branding
LOGO_FONT = "Century Gothic" 
LOGO_COLOR = ACCENT_PRIMARY 

# --- TYPOGRAPHY ---
# MODIF: Reduced font sizes for a more compact and professional look
FONT_FAMILY = "Inter" 
SIZE_TITLE = 15    # Was 18
SIZE_SUBTITLE = 13 # Was 14
SIZE_MAIN = 11     # Was 12
SIZE_SMALL = 9     # Was 10

# --- UI SHAPES & ELEMENTS ---
CORNER_RADIUS = 5  # Slightly sharper
BORDER_WIDTH = 1

# Base Buttons
BTN_PRIMARY = ACCENT_PRIMARY
BTN_PRIMARY_HOVER = ACCENT_PRIMARY_HOVER
BTN_SUCCESS = ACCENT_SUCCESS
BTN_SUCCESS_HOVER = ACCENT_SUCCESS_HOVER
BTN_DANGER = ACCENT_DANGER
BTN_DANGER_HOVER = ACCENT_DANGER_HOVER

# --- CUSTOM WIDGET STYLING KWARGS ---
CHECKBOX_KWARGS = {
    "border_width": 2,             
    "corner_radius": 4,            
    "fg_color": ACCENT_PRIMARY,    
    "hover_color": ACCENT_PRIMARY_HOVER,
    "border_color": ("#A1A1AA", "#52525B"), 
    "checkmark_color": "#FFFFFF",
    "text_color": TEXT_MAIN,
    "font": (FONT_FAMILY, SIZE_MAIN)
}

TABVIEW_KWARGS = {
    "fg_color": "transparent",       
    "segmented_button_fg_color": ("#E4E4E7", "#18181B"), 
    "segmented_button_selected_color": ACCENT_PRIMARY, 
    "segmented_button_selected_hover_color": ACCENT_PRIMARY_HOVER,
    "segmented_button_unselected_color": ("#E4E4E7", "#18181B"),
    "segmented_button_unselected_hover_color": ("#D4D4D8", "#27272A"),
    "text_color": TEXT_MAIN,         
    "corner_radius": 6 # Slightly sharper
}