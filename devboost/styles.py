"""Shared styles and themes for all DevBoost tools.

This module contains standardized QSS (Qt Style Sheets) that provide a consistent
look and feel across all tools in the DevBoost application.
"""

# Main application theme colors
COLORS = {
    # Background colors
    "bg_primary": "#ffffff",
    "bg_secondary": "#f8f9fa",
    "bg_tertiary": "#f0f2f5",
    "bg_sidebar": "#e8e8e8",
    "bg_content": "#f3f3f3",
    
    # Text colors
    "text_primary": "#333333",
    "text_secondary": "#212529",
    "text_muted": "#6c757d",
    "text_placeholder": "#a9a9a9",
    
    # Border colors
    "border_primary": "#dcdcdc",
    "border_secondary": "#dee2e6",
    "border_light": "#e0e0e0",
    "border_focus": "#80bdff",
    
    # Button colors
    "btn_bg": "#f0f0f0",
    "btn_hover": "#e6e6e6",
    "btn_border": "#dcdcdc",
    
    # Status colors
    "success": "#28a745",
    "warning": "#ffc107",
    "error": "#dc3545",
    "info": "#ff8c00",
}

# Font families
FONTS = {
    "ui": '"Segoe UI", Arial, sans-serif',
    "mono": '"Consolas", "Courier New", monospace',
    "system": '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
}

# Layout spacing and margins
LAYOUT = {
    # Standard margins
    "margin_small": 8,
    "margin_medium": 12,
    "margin_large": 15,
    "margin_xlarge": 20,
    
    # Standard spacing
    "spacing_small": 4,
    "spacing_medium": 8,
    "spacing_large": 12,
    "spacing_xlarge": 16,
    
    # Content margins
    "content_margin": 15,
    "section_spacing": 12,
    "toolbar_spacing": 8,
    "button_spacing": 8,
}

# Common widget styles
BASE_WIDGET_STYLE = f"""
QWidget {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    font-family: {FONTS['ui']};
    font-size: 13px;
}}
"""

BUTTON_STYLE = f"""
QPushButton {{
    background-color: {COLORS['btn_bg']};
    border: 1px solid {COLORS['btn_border']};
    padding: 5px 12px;
    border-radius: 4px;
    font-size: 13px;
}}

QPushButton:hover {{
    background-color: {COLORS['btn_hover']};
}}

QPushButton#iconButton {{
    background-color: transparent;
    border: none;
    padding: 4px;
}}

QPushButton#iconButton:hover {{
    background-color: {COLORS['btn_hover']};
    border-radius: 4px;
}}
"""

TEXT_EDIT_STYLE = f"""
QTextEdit {{
    background-color: {COLORS['bg_primary']};
    border: 1px solid {COLORS['border_primary']};
    border-radius: 4px;
    font-family: {FONTS['mono']};
    font-size: 14px;
    padding: 8px;
    color: {COLORS['text_primary']};
}}

QTextEdit:hover {{
    background-color: {COLORS['bg_secondary']};
}}

QTextEdit:focus {{
    border-color: {COLORS['border_focus']};
}}

QTextEdit:read-only {{
    background-color: {COLORS['bg_secondary']};
    color: {COLORS['text_muted']};
}}

QTextEdit::placeholder {{
    color: {COLORS['text_placeholder']};
}}
"""

LINE_EDIT_STYLE = f"""
QLineEdit {{
    background-color: {COLORS['bg_primary']};
    border: 1px solid {COLORS['border_primary']};
    border-radius: 4px;
    padding: 5px 8px;
    font-family: {FONTS['mono']};
    font-size: 13px;
    color: {COLORS['text_primary']};
}}

QLineEdit:hover {{
    background-color: {COLORS['bg_secondary']};
}}

QLineEdit:focus {{
    border-color: {COLORS['border_focus']};
}}
"""

LABEL_STYLE = f"""
QLabel {{
    font-family: {FONTS['ui']};
    font-size: 13px;
    color: {COLORS['text_secondary']};
    font-weight: 500;
}}
"""

COMBOBOX_STYLE = f"""
QComboBox {{
    background-color: {COLORS['bg_primary']};
    border: 1px solid {COLORS['border_primary']};
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 13px;
}}

QComboBox:hover {{
    background-color: {COLORS['bg_secondary']};
}}

QComboBox:focus {{
    border-color: {COLORS['border_focus']};
}}

QComboBox::drop-down {{
    border: none;
}}

QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
}}
"""

SCROLLBAR_STYLE = f"""
QScrollBar:vertical {{
    background-color: {COLORS['bg_secondary']};
    width: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border_primary']};
    border-radius: 6px;
    min-height: 20px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['text_muted']};
}}

QScrollBar::handle:vertical:pressed {{
    background-color: {COLORS['text_secondary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['bg_secondary']};
    height: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['border_primary']};
    border-radius: 6px;
    min-width: 20px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['text_muted']};
}}

QScrollBar::handle:horizontal:pressed {{
    background-color: {COLORS['text_secondary']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    border: none;
    background: none;
    width: 0;
}}
"""

FRAME_STYLE = f"""
QFrame#mainContainer {{
    background-color: {COLORS['bg_primary']};
    border: 1px solid {COLORS['border_secondary']};
    border-radius: 6px;
}}

QFrame#leftPanel {{
    background-color: {COLORS['bg_primary']};
    border-right: 1px solid {COLORS['border_light']};
}}
"""

# Status-specific styles
STATUS_STYLES = {
    "success": f"color: {COLORS['success']};",
    "warning": f"color: {COLORS['warning']};",
    "error": f"color: {COLORS['error']};",
    "info": f"color: {COLORS['info']};",
}

ERROR_INPUT_STYLE = f"""
border: 2px solid {COLORS['error']};
"""

WARNING_INPUT_STYLE = f"""
border: 1px solid {COLORS['warning']};
"""

DIALOG_STYLE = f"""
QDialog {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    font-family: {FONTS['ui']};
}}

QDialog QLabel {{
    font-size: 13px;
    color: {COLORS['text_secondary']};
}}

QDialog QPushButton {{
    background-color: {COLORS['btn_bg']};
    border: 1px solid {COLORS['btn_border']};
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 13px;
    min-width: 80px;
}}

QDialog QPushButton:hover {{
    background-color: {COLORS['btn_hover']};
}}

QDialog QTextEdit {{
    background-color: {COLORS['bg_primary']};
    border: 1px solid {COLORS['border_primary']};
    border-radius: 4px;
    font-family: {FONTS['mono']};
    font-size: 13px;
    padding: 8px;
}}

QDialog QCheckBox {{
    font-size: 13px;
    spacing: 5px;
}}

QDialogButtonBox {{
    background-color: {COLORS['bg_secondary']};
    border-top: 1px solid {COLORS['border_primary']};
}}
"""

# Complete tool widget style
TOOL_WIDGET_STYLE = f"""
{BASE_WIDGET_STYLE}
{BUTTON_STYLE}
{TEXT_EDIT_STYLE}
{LINE_EDIT_STYLE}
{LABEL_STYLE}
{COMBOBOX_STYLE}
{SCROLLBAR_STYLE}
{FRAME_STYLE}
{DIALOG_STYLE}
"""

# Main application styles
MAIN_APP_STYLE = f"""
QMainWindow {{
    background-color: {COLORS['bg_sidebar']};
}}

#sidebar {{
    background-color: {COLORS['bg_sidebar']};
    border-right: 1px solid {COLORS['border_primary']};
}}

#contentArea {{
    background-color: {COLORS['bg_content']};
}}

#topBar {{
    background-color: {COLORS['bg_sidebar']};
    border-bottom: 1px solid {COLORS['border_primary']};
}}

#topBarTitle {{
    font-size: 14px;
    font-weight: bold;
    color: {COLORS['text_primary']};
}}

#appName {{
    font-size: 28px;
    font-weight: bold;
    color: {COLORS['text_primary']};
}}

#infoLabel {{
    font-size: 14px;
    color: {COLORS['text_muted']};
}}
"""


def get_tool_style():
    """Get the standard style for tool widgets.
    
    Returns:
        str: Complete QSS stylesheet for tool widgets.
    """
    return TOOL_WIDGET_STYLE


def get_main_app_style():
    """Get the style for the main application window.
    
    Returns:
        str: Complete QSS stylesheet for main application.
    """
    return MAIN_APP_STYLE


def get_status_style(status_type):
    """Get style for status indicators.
    
    Args:
        status_type (str): Type of status ('success', 'warning', 'error', 'info')
        
    Returns:
        str: QSS style for the status type.
    """
    return STATUS_STYLES.get(status_type, STATUS_STYLES['info'])


def get_error_input_style():
    """Get style for input fields with errors.
    
    Returns:
        str: QSS style for error state inputs.
    """
    return ERROR_INPUT_STYLE


def get_warning_input_style():
    """Get style for input fields with warnings.
    
    Returns:
        str: QSS style for warning state inputs.
    """
    return WARNING_INPUT_STYLE


def get_dialog_style():
    """Get the standard style for dialog windows.
    
    Returns:
        str: Complete QSS stylesheet for dialogs.
    """
    return DIALOG_STYLE


def get_layout_margin(size="medium"):
    """Get standard layout margin.
    
    Args:
        size (str): Size of margin ('small', 'medium', 'large', 'xlarge')
        
    Returns:
        int: Margin value in pixels.
    """
    return LAYOUT.get(f"margin_{size}", LAYOUT["margin_medium"])


def get_layout_spacing(size="medium"):
    """Get standard layout spacing.
    
    Args:
        size (str): Size of spacing ('small', 'medium', 'large', 'xlarge')
        
    Returns:
        int: Spacing value in pixels.
    """
    return LAYOUT.get(f"spacing_{size}", LAYOUT["spacing_medium"])


def get_content_margin():
    """Get standard content margin.
    
    Returns:
        int: Content margin value in pixels.
    """
    return LAYOUT["content_margin"]


def get_section_spacing():
    """Get standard section spacing.
    
    Returns:
        int: Section spacing value in pixels.
    """
    return LAYOUT["section_spacing"]


def clear_input_style():
    """Get style to clear error/warning states from inputs.
    
    Returns:
        str: Empty string to clear custom styles.
    """
    return ""