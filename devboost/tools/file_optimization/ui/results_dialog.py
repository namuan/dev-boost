from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from devboost.tools.file_optimization.models import BatchOperationResult, BatchProgress


class OptimizationResultsDialog(QDialog):
    """Dialog to display detailed optimization results."""

    def __init__(self, results: list[BatchOperationResult], batch_progress: BatchProgress, parent=None):
        super().__init__(parent)
        self.results = results
        self.batch_progress = batch_progress
        self.setWindowTitle("Optimization Results")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        """Setup the results dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Summary section
        summary_frame = self._create_summary_section()
        layout.addWidget(summary_frame)

        # Results table
        results_table = self._create_results_table()
        layout.addWidget(results_table)

        # Button section
        button_layout = self._create_button_section()
        layout.addLayout(button_layout)

    def _create_summary_section(self) -> QFrame:
        """Create the summary section showing overall statistics."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        frame.setStyleSheet(
            """
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
            """
        )

        layout = QGridLayout(frame)
        layout.setSpacing(10)

        # Calculate statistics
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]

        total_original_size = sum(r.original_size for r in successful)
        total_optimized_size = sum(r.optimized_size for r in successful)
        total_size_reduction = total_original_size - total_optimized_size

        overall_compression = total_size_reduction / total_original_size * 100 if total_original_size > 0 else 0.0

        total_processing_time = sum(r.processing_time for r in self.results)

        # Summary labels
        summary_data = [
            ("Total Files:", f"{len(self.results)}"),
            ("Successful:", f"{len(successful)}"),
            ("Failed:", f"{len(failed)}"),
            ("Success Rate:", f"{len(successful) / len(self.results) * 100:.1f}%" if self.results else "0%"),
            ("Total Original Size:", self.batch_progress.format_size(total_original_size)),
            ("Total Optimized Size:", self.batch_progress.format_size(total_optimized_size)),
            ("Space Saved:", self.batch_progress.format_size(total_size_reduction)),
            ("Compression Ratio:", f"{overall_compression:.1f}%"),
            ("Processing Time:", self.batch_progress.format_time(total_processing_time)),
            (
                "Average Speed:",
                f"{len(self.results) / total_processing_time:.1f} files/s" if total_processing_time > 0 else "N/A",
            ),
        ]

        for i, (label, value) in enumerate(summary_data):
            row, col = divmod(i, 2)

            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-weight: bold; color: #495057;")

            value_widget = QLabel(value)
            value_widget.setStyleSheet("color: #212529;")

            layout.addWidget(label_widget, row, col * 2)
            layout.addWidget(value_widget, row, col * 2 + 1)

        return frame

    def _create_results_table(self) -> QTableWidget:
        """Create the detailed results table."""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "File",
            "Status",
            "Original Size",
            "Optimized Size",
            "Compression",
            "Method",
            "Processing Time",
        ])

        # Set table properties
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSortingEnabled(True)
        table.verticalHeader().setVisible(False)

        # Populate table
        table.setRowCount(len(self.results))

        for row, result in enumerate(self.results):
            # File name
            file_item = QTableWidgetItem(result.file_path.name)
            file_item.setToolTip(str(result.file_path))
            table.setItem(row, 0, file_item)

            # Status
            status_item = QTableWidgetItem("✅ Success" if result.success else "❌ Failed")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if result.success:
                status_item.setBackground(QColor("#d4edda"))
            else:
                status_item.setBackground(QColor("#f8d7da"))
                status_item.setToolTip(result.error_message or "Unknown error")
            table.setItem(row, 1, status_item)

            if result.success:
                # Original size
                original_size_item = QTableWidgetItem(self.batch_progress.format_size(result.original_size))
                original_size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                table.setItem(row, 2, original_size_item)

                # Optimized size
                optimized_size_item = QTableWidgetItem(self.batch_progress.format_size(result.optimized_size))
                optimized_size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
                table.setItem(row, 3, optimized_size_item)

                # Compression ratio
                compression = (
                    (result.original_size - result.optimized_size) / result.original_size * 100
                    if result.original_size > 0
                    else 0.0
                )
                compression_item = QTableWidgetItem(f"{compression:.1f}%")
                compression_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Color code compression ratio
                if compression > 20:
                    compression_item.setBackground(QColor("#d4edda"))  # Green for good compression
                elif compression > 5:
                    compression_item.setBackground(QColor("#fff3cd"))  # Yellow for moderate compression
                else:
                    compression_item.setBackground(QColor("#f8d7da"))  # Red for poor compression

                table.setItem(row, 4, compression_item)

                # Method
                method_item = QTableWidgetItem(result.method_used or "Unknown")
                method_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, 5, method_item)
            else:
                # Fill empty cells for failed files
                for col in range(2, 6):
                    empty_item = QTableWidgetItem("N/A")
                    empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    empty_item.setForeground(QColor("#6c757d"))
                    table.setItem(row, col, empty_item)

            # Processing time
            time_item = QTableWidgetItem(self.batch_progress.format_time(result.processing_time))
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 6, time_item)

        # Resize columns to content
        table.resizeColumnsToContents()

        # Set minimum column widths
        header = table.horizontalHeader()
        header.setMinimumSectionSize(80)
        header.setStretchLastSection(True)

        return table

    def _create_button_section(self) -> QHBoxLayout:
        """Create the button section."""
        layout = QHBoxLayout()
        layout.addStretch()

        # Export button
        export_button = QPushButton("Export Results")
        export_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        export_button.clicked.connect(self._export_results)
        layout.addWidget(export_button)

        # Close button
        close_button = QPushButton("Close")
        close_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton))
        close_button.clicked.connect(self.accept)
        close_button.setDefault(True)
        layout.addWidget(close_button)

        return layout

    def _export_results(self):
        """Export results to a text file."""

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Optimization Results",
            f"optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)",
        )

        if not file_path:
            return

        try:
            with Path(file_path).open("w", encoding="utf-8") as f:
                f.write("File Optimization Results\n")
                f.write("=" * 50 + "\n\n")

                # Summary
                successful = [r for r in self.results if r.success]
                failed = [r for r in self.results if not r.success]

                total_original_size = sum(r.original_size for r in successful)
                total_optimized_size = sum(r.optimized_size for r in successful)
                total_size_reduction = total_original_size - total_optimized_size

                overall_compression = (
                    total_size_reduction / total_original_size * 100 if total_original_size > 0 else 0.0
                )

                total_processing_time = sum(r.processing_time for r in self.results)

                f.write("Summary:\n")
                f.write(f"  Total Files: {len(self.results)}\n")
                f.write(f"  Successful: {len(successful)}\n")
                f.write(f"  Failed: {len(failed)}\n")
                f.write(f"  Success Rate: {len(successful) / len(self.results) * 100:.1f}%\n")
                f.write(f"  Total Original Size: {self.batch_progress.format_size(total_original_size)}\n")
                f.write(f"  Total Optimized Size: {self.batch_progress.format_size(total_optimized_size)}\n")
                f.write(f"  Space Saved: {self.batch_progress.format_size(total_size_reduction)}\n")
                f.write(f"  Compression Ratio: {overall_compression:.1f}%\n")
                f.write(f"  Processing Time: {self.batch_progress.format_time(total_processing_time)}\n\n")

                # Detailed results
                f.write("Detailed Results:\n")
                f.write("-" * 50 + "\n")

                for result in self.results:
                    f.write(f"\nFile: {result.file_path.name}\n")
                    f.write(f"  Status: {'Success' if result.success else 'Failed'}\n")

                    if result.success:
                        compression = (
                            (result.original_size - result.optimized_size) / result.original_size * 100
                            if result.original_size > 0
                            else 0.0
                        )
                        f.write(f"  Original Size: {self.batch_progress.format_size(result.original_size)}\n")
                        f.write(f"  Optimized Size: {self.batch_progress.format_size(result.optimized_size)}\n")
                        f.write(f"  Compression: {compression:.1f}%\n")
                        f.write(f"  Method: {result.method_used or 'Unknown'}\n")
                    else:
                        f.write(f"  Error: {result.error_message or 'Unknown error'}\n")

                    f.write(f"  Processing Time: {self.batch_progress.format_time(result.processing_time)}\n")

            QMessageBox.information(self, "Export Successful", f"Results exported successfully to:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export results:\n{e!s}")
