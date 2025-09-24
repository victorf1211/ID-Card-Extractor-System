import csv
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ClassVar, TypedDict

from .llm_extractor import IDCardFields

logger = logging.getLogger(__name__)


class ExportResult(TypedDict):
    """Result of data export operation."""

    success: bool
    file_path: str | None
    error_message: str | None
    warnings: list[str]


class DataExporter:
    """Handles data export and validation for ID card information."""

    _REQUIRED_FRONT_FIELDS: ClassVar[frozenset[str]] = frozenset(
        {"name", "birth_date", "issue_date", "gender", "id_number"}
    )
    _REQUIRED_BACK_FIELDS: ClassVar[frozenset[str]] = frozenset({"address"})
    _DATE_FORMAT: ClassVar[str] = "%Y-%m-%d"
    _ID_NUMBER_LENGTH: ClassVar[int] = 10

    def __init__(self, output_dir: str | Path) -> None:
        """Initialize the data exporter.

        Args:
            output_dir: Directory where CSV files will be saved
        """
        self.output_dir = Path(output_dir)
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_to_csv(self, fields: IDCardFields, id_number: str | None = None) -> ExportResult:
        """Export ID card fields to CSV format.

        Args:
            fields: Extracted fields from ID card
            id_number: Optional ID number for filename (if None, uses timestamp)

        Returns:
            ExportResult: Result of the export operation
        """
        try:
            id_number = id_number or fields.get("id_number")
            if not id_number:
                id_number = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            data = {k: str(v) if v is not None else "" for k, v in fields.items()}
            filename = f"idcard_{id_number}.csv"
            filepath = self.output_dir / filename

            # Write to CSV with UTF-8 BOM for Excel
            fieldnames = [
                "name",
                "birth_date",
                "issue_date",
                "gender",
                "id_number",
                "father_name",
                "mother_name",
                "spouse_name",
                "military_service",
                "birth_place",
                "address",
            ]
            with filepath.open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(data)
            return {
                "success": True,
                "file_path": str(filepath),
                "error_message": None,
                "warnings": [],
            }
        except (OSError, csv.Error) as e:
            logger.error(f"Failed to export CSV: {e}")
            return {"success": False, "file_path": None, "error_message": str(e), "warnings": []}

    def _validate_fields(self, fields: IDCardFields) -> dict[str, Any]:
        """Validate the completeness and format of extracted fields.

        Args:
            fields: Extracted fields to validate

        Returns:
            dict: Validation result with success status and error message
        """
        # List all fields that should be present
        required_fields: list[str] = []
        recommended_fields = ["name", "id_number", "birth_date"]

        # Check which fields are missing
        missing_required = [f for f in required_fields if not fields.get(f)]
        missing_recommended = [f for f in recommended_fields if not fields.get(f)]

        return {
            "is_valid": len(missing_required) == 0,  # Only fail if required fields are missing
            "missing_fields": {"required": missing_required, "recommended": missing_recommended},
        }

    def _prepare_csv_data(self, fields: IDCardFields) -> dict[str, str]:
        """Prepare fields for CSV export with proper formatting.

        Args:
            fields: Extracted fields to format

        Returns:
            dict: Formatted field values ready for CSV export
        """
        # Convert all fields to strings, using empty string for None values
        return {k: str(v) if v is not None else "" for k, v in fields.items()}

    def _is_valid_id_number(self, id_number: str) -> bool:
        """Validate Taiwan ID number format.

        Args:
            id_number: ID number to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not id_number:
            return False

        # Taiwan ID format: A123456789
        if len(id_number) != self._ID_NUMBER_LENGTH:
            return False

        if not (id_number[0].isalpha() and id_number[1:].isdigit()):
            return False

        return id_number[1] in "12"  # Second digit must be 1 or 2
