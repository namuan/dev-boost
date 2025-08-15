import logging
import re
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStyle,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..styles import clear_input_style, get_dialog_style, get_error_input_style, get_tool_style

logger = logging.getLogger(__name__)


class RegexCheatSheetDialog(QDialog):
    """Cheat sheet dialog for regex syntax help."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Regex Cheat Sheet")
        self.setModal(True)
        self.setFixedSize(600, 500)

        self.setup_ui()

    def setup_ui(self):
        """Setup the cheat sheet dialog UI."""
        self.setStyleSheet(get_dialog_style())

        layout = QVBoxLayout(self)

        # Create text area for cheat sheet content
        cheat_sheet_text = QTextEdit()
        cheat_sheet_text.setReadOnly(True)
        cheat_sheet_text.setPlainText(self.get_cheat_sheet_content())
        layout.addWidget(cheat_sheet_text)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def get_cheat_sheet_content(self):
        """Get the cheat sheet content."""
        return """REGEX CHEAT SHEET

=== CHARACTER CLASSES ===
.          Any character except newline
\\d         Digit (0-9)
\\D         Non-digit
\\w         Word character (a-z, A-Z, 0-9, _)
\\W         Non-word character
\\s         Whitespace (space, tab, newline)
\\S         Non-whitespace

=== ANCHORS ===
^          Start of string/line
$          End of string/line
\b         Word boundary
\\B         Non-word boundary

=== QUANTIFIERS ===
*          0 or more
+          1 or more
?          0 or 1
{n}        Exactly n times
{n,}       n or more times
{n,m}      Between n and m times

=== GROUPS ===
(...)      Capturing group
(?:...)    Non-capturing group
(?P<name>...) Named group

=== CHARACTER SETS ===
[abc]      Any of a, b, or c
[a-z]      Any lowercase letter
[A-Z]      Any uppercase letter
[0-9]      Any digit
[^abc]     Not a, b, or c

=== SPECIAL CHARACTERS ===
\\          Escape character
|          OR operator

=== FLAGS ===
i          Case insensitive
m          Multiline mode
s          Dot matches all (including newline)

=== EXAMPLES ===
\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\b
           Email address

\\(?\\d{3}\\)?[-. ]?\\d{3}[-.]?\\d{4}
           Phone number

\\d{4}-\\d{2}-\\d{2}
           Date (YYYY-MM-DD)

^https?://[^\\s]+
           URL starting with http/https"""


class RegexSettingsDialog(QDialog):
    """Settings dialog for regex options."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Regex Settings")
        self.setModal(True)
        self.setFixedSize(300, 200)

        # Initialize flags
        self.case_insensitive = False
        self.multiline = False
        self.dotall = False

        self.setup_ui()

    def setup_ui(self):
        """Setup the settings dialog UI."""
        self.setStyleSheet(get_dialog_style())

        layout = QVBoxLayout(self)

        # Case insensitive option
        self.case_checkbox = QCheckBox("Case insensitive (re.IGNORECASE)")
        self.case_checkbox.setChecked(self.case_insensitive)
        layout.addWidget(self.case_checkbox)

        # Multiline option
        self.multiline_checkbox = QCheckBox("Multiline mode (re.MULTILINE)")
        self.multiline_checkbox.setChecked(self.multiline)
        layout.addWidget(self.multiline_checkbox)

        # Dotall option
        self.dotall_checkbox = QCheckBox("Dot matches all (re.DOTALL)")
        self.dotall_checkbox.setChecked(self.dotall)
        layout.addWidget(self.dotall_checkbox)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def get_flags(self):
        """Get the regex flags based on current settings."""
        flags = 0
        if self.case_checkbox.isChecked():
            flags |= re.IGNORECASE
        if self.multiline_checkbox.isChecked():
            flags |= re.MULTILINE
        if self.dotall_checkbox.isChecked():
            flags |= re.DOTALL
        return flags


class RegexTester:
    """Backend logic for regex testing functionality."""

    def __init__(self):
        """Initialize the RegexTester."""
        self.pattern = ""
        self.text = ""
        self.flags = 0

    def set_pattern(self, pattern: str) -> bool:
        """
        Set the regex pattern and validate it.

        Args:
            pattern: The regex pattern string

        Returns:
            bool: True if pattern is valid, False otherwise
        """
        try:
            re.compile(pattern)
            self.pattern = pattern
            return True
        except re.error:
            return False

    def set_text(self, text: str) -> None:
        """
        Set the text to test against.

        Args:
            text: The text to test
        """
        self.text = text

    def find_matches(self) -> list[tuple[str, int, int]]:
        """
        Find all matches in the text.

        Returns:
            List of tuples containing (match_text, start_pos, end_pos)
        """
        if not self.pattern or not self.text:
            return []

        try:
            pattern = re.compile(self.pattern, self.flags)
            matches = []
            for match in pattern.finditer(self.text):
                matches.append((match.group(), match.start(), match.end()))
            return matches
        except re.error:
            return []

    def get_match_count(self) -> int:
        """
        Get the number of matches.

        Returns:
            int: Number of matches found
        """
        return len(self.find_matches())

    def replace_matches(self, replacement: str) -> str:
        """
        Replace all matches with the replacement string.

        Args:
            replacement: The replacement string

        Returns:
            str: Text with replacements made
        """
        if not self.pattern or not self.text:
            return self.text

        try:
            pattern = re.compile(self.pattern, self.flags)
            return pattern.sub(replacement, self.text)
        except re.error:
            return self.text

    def format_output(self, output_format: str) -> str:
        """
        Format matches according to the output format string.

        Args:
            output_format: Format string (e.g., "$&\\n" for match + newline)

        Returns:
            str: Formatted output
        """
        matches = self.find_matches()
        if not matches:
            return ""

        result = []
        for match_text, _, _ in matches:
            formatted = output_format.replace("$&", match_text)
            formatted = formatted.replace("\\n", "\n")
            formatted = formatted.replace("\\t", "\t")
            result.append(formatted)

        return "".join(result)

    def get_sample_pattern(self) -> str:
        """
        Get a sample regex pattern for demonstration.

        Returns:
            str: Sample regex pattern
        """
        return r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"


# ruff: noqa: C901
def create_regexp_tester_widget(style_func, scratch_pad=None):
    """
    Creates and returns the RegExp Tester widget.

    Args:
        style_func: Function to get QStyle for standard icons.
        scratch_pad: Optional scratch pad widget to send results to.

    Returns:
        QWidget: The complete RegExp Tester widget.
    """
    logger.info("Creating RegExp Tester widget")
    widget = QWidget()

    # Create backend instance
    regex_tester = RegexTester()
    widget.setStyleSheet(get_tool_style())

    # --- MAIN LAYOUT ---
    main_layout = QVBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # --- REGEXP SECTION ---
    regexp_section_frame = QFrame()
    regexp_section_layout = QVBoxLayout(regexp_section_frame)
    regexp_section_layout.setContentsMargins(1, 1, 1, 1)  # Thin margins for inner layout
    regexp_top_bar_layout = QHBoxLayout()
    regexp_top_bar_layout.setContentsMargins(10, 5, 5, 10)
    regexp_top_bar_layout.setSpacing(5)

    regexp_label = QLabel("RegExp:")
    regexp_input = QLineEdit()
    regexp_input.setPlaceholderText("Enter a regular expression")
    regexp_input.setObjectName("barInput")

    clipboard_button_1 = QPushButton("Clipboard")
    sample_button = QPushButton("Sample")
    clear_button = QPushButton("Clear")

    settings_button = QPushButton()
    settings_button.setObjectName("iconButton")
    # Image description: A flat, gray gear icon for settings.
    settings_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))

    cheat_sheet_button = QPushButton("Cheat Sheet")
    # Image description: A document or book icon, for a cheat sheet.
    cheat_sheet_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_DialogHelpButton))
    cheat_sheet_button.setObjectName("cheatSheetButton")

    regexp_top_bar_layout.addWidget(regexp_label)
    regexp_top_bar_layout.addSpacing(5)
    regexp_top_bar_layout.addWidget(regexp_input, 1)
    regexp_top_bar_layout.addWidget(clipboard_button_1)
    regexp_top_bar_layout.addWidget(sample_button)
    regexp_top_bar_layout.addWidget(clear_button)
    regexp_top_bar_layout.addWidget(settings_button)
    regexp_top_bar_layout.addStretch()
    regexp_top_bar_layout.addWidget(cheat_sheet_button)
    regexp_section_layout.addLayout(regexp_top_bar_layout)
    regexp_section_layout.setStretchFactor(regexp_top_bar_layout, 0)

    # --- TEXT INPUT SECTION ---
    text_section_frame = QFrame()
    text_section_layout = QVBoxLayout(text_section_frame)
    text_section_layout.setContentsMargins(10, 10, 10, 10)
    text_section_layout.setSpacing(8)

    text_top_bar_layout = QHBoxLayout()
    text_top_bar_layout.setSpacing(8)
    text_label = QLabel("Text:")
    clipboard_button_2 = QPushButton("Clipboard")
    matches_label = QLabel("0 matches")
    matches_label.setAlignment(Qt.AlignmentFlag.AlignRight)

    text_top_bar_layout.addWidget(text_label)
    text_top_bar_layout.addWidget(clipboard_button_2)
    text_top_bar_layout.addStretch()
    text_top_bar_layout.addWidget(matches_label)
    text_section_layout.addLayout(text_top_bar_layout)

    text_input_edit = QTextEdit()
    text_section_layout.addWidget(text_input_edit)

    # --- BOTTOM SECTION (OUTPUT & MATCHES) ---
    bottom_layout = QHBoxLayout()
    bottom_layout.setSpacing(12)

    # --- OUTPUT (Left Side) ---
    output_section_frame = QFrame()
    output_section_layout = QVBoxLayout(output_section_frame)
    output_section_layout.setContentsMargins(10, 10, 10, 10)
    output_section_layout.setSpacing(8)

    output_top_bar_layout = QHBoxLayout()
    output_top_bar_layout.setSpacing(8)
    output_label = QLabel("Output:")
    output_input = QLineEdit("$&\\n")
    output_input.setObjectName("barInput")
    help_button = QPushButton()
    help_button.setObjectName("iconButton")
    # Image description: A question mark icon inside a circle.
    help_button.setIcon(style_func().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion))

    # Add "Send to Scratch Pad" button if scratch_pad is provided
    send_to_scratch_pad_button = None
    if scratch_pad:
        send_to_scratch_pad_button = QPushButton("Send to Scratch Pad")

    output_top_bar_layout.addWidget(output_label)
    output_top_bar_layout.addSpacing(5)
    output_top_bar_layout.addWidget(output_input, 1)
    output_top_bar_layout.addWidget(help_button)
    if send_to_scratch_pad_button:
        output_top_bar_layout.addWidget(send_to_scratch_pad_button)
    output_top_bar_layout.addStretch()

    output_text_edit = QTextEdit()
    output_text_edit.setReadOnly(True)
    output_section_layout.addLayout(output_top_bar_layout)
    output_section_layout.addWidget(output_text_edit, 1)
    bottom_layout.addWidget(output_section_frame, 1)

    # --- MATCHES (Right Side) ---
    matches_section_frame = QFrame()
    matches_section_layout = QVBoxLayout(matches_section_frame)
    matches_section_layout.setContentsMargins(10, 10, 10, 10)
    matches_section_layout.setSpacing(8)

    matches_top_bar_layout = QHBoxLayout()
    matches_top_bar_layout.setSpacing(8)
    copy_button = QPushButton("Copy")
    # Image description: A copy icon. Two overlapping squares or pages.
    search_matches_input = QLineEdit()
    search_matches_input.setPlaceholderText("Search matches...")
    # Image description: Placeholder for a magnifying glass search icon.
    search_icon = style_func().standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView)
    search_action = QAction(search_icon, "Search", search_matches_input)
    search_matches_input.addAction(search_action, QLineEdit.ActionPosition.LeadingPosition)
    search_matches_input.setProperty("has-leading-action", True)  # For styling

    matches_top_bar_layout.addStretch()
    matches_top_bar_layout.addWidget(copy_button)
    matches_top_bar_layout.addWidget(search_matches_input, 1)

    matches_text_edit = QTextEdit()
    matches_text_edit.setReadOnly(True)
    matches_section_layout.addLayout(matches_top_bar_layout)
    matches_section_layout.addWidget(matches_text_edit, 1)
    bottom_layout.addWidget(matches_section_frame, 1)

    # --- Add all sections to the main layout ---
    main_layout.addWidget(regexp_section_frame)
    main_layout.addWidget(text_section_frame, 4)
    main_layout.addLayout(bottom_layout, 3)

    # --- FUNCTIONALITY CONNECTIONS ---
    # Store matches for later use in formatting
    current_matches = []

    def update_results():
        """Update the results based on current pattern and text."""
        nonlocal current_matches

        pattern = regexp_input.text()
        text = text_input_edit.toPlainText()
        output_format = output_input.text()

        # Set pattern and text in backend
        regex_tester.set_text(text)
        is_valid = regex_tester.set_pattern(pattern)

        if not is_valid and pattern:
            # Invalid pattern - show error styling
            regexp_input.setStyleSheet(get_error_input_style())
            matches_label.setText("Invalid pattern")
            output_text_edit.clear()
            matches_text_edit.clear()
            current_matches = []
            return
        else:
            # Valid pattern - reset styling
            regexp_input.setStyleSheet(clear_input_style())

        # Update match count
        match_count = regex_tester.get_match_count()
        matches_label.setText(f"{match_count} matches")

        # Update output
        if pattern and text:
            formatted_output = regex_tester.format_output(output_format)
            output_text_edit.setPlainText(formatted_output)

            # Update matches display
            matches = regex_tester.find_matches()
            current_matches = matches  # Store for later use
            matches_display = []
            for i, (match_text, start, end) in enumerate(matches, 1):
                matches_display.append(f"{i}. {match_text} (pos {start}-{end})")
            matches_text_edit.setPlainText("\n".join(matches_display))
        else:
            output_text_edit.clear()
            matches_text_edit.clear()
            current_matches = []

    def on_sample_clicked():
        """Load a sample pattern and text."""
        sample_pattern = regex_tester.get_sample_pattern()
        sample_text = "Contact us at: john.doe@example.com or support@company.org\nInvalid emails: notanemail, @invalid.com, test@"

        regexp_input.setText(sample_pattern)
        text_input_edit.setPlainText(sample_text)
        update_results()

    def on_clear_clicked():
        """Clear the pattern input."""
        regexp_input.clear()
        update_results()

    def on_clipboard_pattern_clicked():
        """Copy pattern to clipboard."""
        from PyQt6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(regexp_input.text())

    def on_clipboard_text_clicked():
        """Copy text to clipboard."""
        from PyQt6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(text_input_edit.toPlainText())

    def on_copy_matches_clicked():
        """Copy matches to clipboard."""
        from PyQt6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(matches_text_edit.toPlainText())

    def on_settings_clicked():
        """Open settings dialog."""
        dialog = RegexSettingsDialog(widget)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update regex tester flags
            regex_tester.flags = dialog.get_flags()
            # Refresh results with new flags
            update_results()

    def on_cheat_sheet_clicked():
        """Open cheat sheet dialog."""
        dialog = RegexCheatSheetDialog(widget)
        dialog.exec()

    def filter_matches():
        """Filter matches based on search input."""
        search_term = search_matches_input.text().lower()
        if not search_term:
            # Show all matches if no search term
            matches = regex_tester.find_matches()
            matches_display = []
            for i, (match_text, start, end) in enumerate(matches, 1):
                matches_display.append(f"{i}. {match_text} (pos {start}-{end})")
            matches_text_edit.setPlainText("\n".join(matches_display))
        else:
            # Filter matches containing the search term
            matches = regex_tester.find_matches()
            filtered_matches = []
            for i, (match_text, start, end) in enumerate(matches, 1):
                if search_term in match_text.lower():
                    filtered_matches.append(f"{i}. {match_text} (pos {start}-{end})")
            matches_text_edit.setPlainText("\n".join(filtered_matches))

    # Connect signals
    regexp_input.textChanged.connect(update_results)
    text_input_edit.textChanged.connect(update_results)
    output_input.textChanged.connect(update_results)

    sample_button.clicked.connect(on_sample_clicked)
    clear_button.clicked.connect(on_clear_clicked)
    clipboard_button_1.clicked.connect(on_clipboard_pattern_clicked)
    clipboard_button_2.clicked.connect(on_clipboard_text_clicked)
    copy_button.clicked.connect(on_copy_matches_clicked)
    settings_button.clicked.connect(on_settings_clicked)
    cheat_sheet_button.clicked.connect(on_cheat_sheet_clicked)
    search_matches_input.textChanged.connect(filter_matches)

    # Connect "Send to Scratch Pad" button if it exists
    if send_to_scratch_pad_button:

        def on_send_to_scratch_pad():
            # Get current state for formatting
            pattern = regexp_input.text()
            text = text_input_edit.toPlainText()
            output_text = output_text_edit.toPlainText()

            # Format with context
            formatted_content = format_regexp_output_for_scratch_pad(pattern, text, current_matches, output_text)
            send_to_scratch_pad(scratch_pad, formatted_content)

        send_to_scratch_pad_button.clicked.connect(on_send_to_scratch_pad)

    logger.info("RegExp Tester widget creation completed")
    return widget


def send_to_scratch_pad(scratch_pad, content):
    """
    Send content to the scratch pad.

    Args:
        scratch_pad: The scratch pad widget.
        content (str): The content to send.
    """
    if scratch_pad and content:
        # Append content to the scratch pad with a separator
        current_content = scratch_pad.get_content()
        new_content = f"{current_content}\n\n---\n{content}" if current_content else content
        scratch_pad.set_content(new_content)


def format_regexp_output_for_scratch_pad(pattern, text, matches, output_text):
    """
    Format RegExp Tester output for sending to scratch pad with context.

    Args:
        pattern (str): The regex pattern used
        text (str): The input text
        matches (list): List of matches found
        output_text (str): The formatted output text

    Returns:
        str: Formatted content for scratch pad
    """
    # Create a header with context
    header = f"RegExp Tester Results\nPattern: {pattern}\nMatches Found: {len(matches)}\n" + "=" * 50

    # Format matches with details
    matches_section = "MATCHES:\n"
    for i, (match_text, start, end) in enumerate(matches, 1):
        matches_section += f"{i}. '{match_text}' (position {start}-{end})\n"

    # Add the formatted output
    output_section = f"\nFORMATTED OUTPUT:\n{output_text}"

    # Add the original text for reference
    text_section = f"\nINPUT TEXT:\n{text}"

    return f"{header}\n\n{matches_section}\n{output_section}\n{text_section}"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    app = QApplication(sys.argv)

    main_window = QMainWindow()
    main_window.setWindowTitle("RegExp Tester")
    main_window.setGeometry(100, 100, 1100, 750)

    regexp_tool_widget = create_regexp_tester_widget(app.style)
    main_window.setCentralWidget(regexp_tool_widget)

    main_window.show()
    sys.exit(app.exec())
