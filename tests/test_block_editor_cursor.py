import pytest
from PyQt6.QtWidgets import QApplication

from devboost.tools.block_editor.storage import Block
from devboost.tools.block_editor.widget import BlockWidget


# Ensure QApplication exists
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_calc_cursor_position(qapp):
    """
    Verify that the cursor position is preserved/adjusted correctly
    after a calculation is applied.
    """
    # Create a block with 'calc' language
    block = Block(id="test-block", title="Test Block", order=0, content="", language="calc")
    widget = BlockWidget(block)

    # Get the active editor (should be QTextEdit for calc)
    editor = widget.editor

    # Simulate typing "1+1" first
    widget.set_content("1+1")

    # Move cursor to the end
    cursor = editor.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    editor.setTextCursor(cursor)

    # Simulate typing "="
    # This triggers the calculation immediately via textChanged signal
    editor.insertPlainText("=")

    # Verify the content was updated
    # If the signal worked, it should be "1+1 = 2"
    expected_content = "1+1 = 2"
    assert widget.get_content() == expected_content

    # Verify cursor position
    # The cursor should be at the end of the line
    current_pos = editor.textCursor().position()
    assert current_pos == len(expected_content), f"Cursor position {current_pos} != {len(expected_content)}"
