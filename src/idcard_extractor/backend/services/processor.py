from pathlib import Path
from typing import Literal, TypedDict, cast

import cv2
import numpy as np
from numpy.typing import NDArray

from .csv_exporter import DataExporter, ExportResult
from .id_detector import IDCardDetector
from .image_processor import ImagePreprocessor
from .llm_extractor import IDCardFields, LLMFieldExtractor

# Type alias for OpenCV images
ImageType = NDArray[np.uint8]


class IDCardResult(TypedDict):
    """Result of ID card processing."""

    preprocessed_image: ImageType  # Image after preprocessing
    card_region: ImageType  # Cropped ID card image
    standardized_image: ImageType  # Size-standardized image
    side: Literal["front", "back"]  # Front or back side
    contour_points: list[list[int]]  # Detected card contour points
    fields: IDCardFields  # Extracted fields
    export_result: ExportResult | None  # Export result


class IDCardProcessor:
    """Integrated processor for ID card extraction and recognition."""

    def __init__(self, output_dir: str | Path | None = None) -> None:
        """Initialize processors.

        Args:
            output_dir: Optional directory for saving CSV output
        """
        self.preprocessor = ImagePreprocessor()
        self.detector = IDCardDetector()
        self.field_extractor = LLMFieldExtractor()
        self.data_exporter = DataExporter(output_dir) if output_dir else None

    def process(
        self,
        image_path: str | Path,
        export_csv: bool = False,
        side: str | None = None,
    ) -> IDCardResult:
        """Process ID card image through all steps."""
        # Step 1: Image preprocessing (just basic preprocessing, no OCR)
        preprocessed = self.preprocessor.preprocess(image_path)
        processed = self.preprocessor.process_image(preprocessed)

        # Step 2: Detect and extract card region
        card_image, contour = self.detector.detect_card_region(processed)

        # Step 3: Standardize image size
        standardized = self.detector.standardize_image(card_image)

        # Step 4: Apply binary thresholding
        gray = cv2.cvtColor(standardized, cv2.COLOR_BGR2GRAY)
        # Increase contrast
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=-50)
        # Apply Otsu's thresholding
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # Convert back to BGR for LLM input
        binary_bgr = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        cv2.imwrite("data/output/binary_id_card.jpg", binary_bgr)

        # Step 5: Use provided side, or default to front if not provided
        side_detected = side if side is not None else "front"

        # Step 6: Extract fields using LLM
        fields = self.field_extractor.extract_fields(
            binary_bgr, cast("Literal['front', 'back']", side_detected)
        )

        # Step 7: Export to CSV if requested
        export_result = None
        if export_csv and self.data_exporter:
            export_result = self.data_exporter.export_to_csv(
                fields, id_number=fields.get("id_number")
            )

        return {
            "preprocessed_image": preprocessed,
            "card_region": card_image,
            "standardized_image": standardized,
            "side": cast("Literal['front', 'back']", side_detected),
            "contour_points": contour,
            "fields": fields,
            "export_result": export_result,
        }
