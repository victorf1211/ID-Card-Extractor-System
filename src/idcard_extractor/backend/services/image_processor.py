# ruff: noqa: RUF100  # Ignore unknown word warnings

import logging
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

# More specific type alias for OpenCV images
ImageType = NDArray[np.uint8]
FloatImage = NDArray[np.float32]

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    _MIN_ANGLE = 45
    _MAX_ANGLE = 135
    _RGB_CHANNELS = 3
    _ANGLE_THRESHOLD = 90
    _FULL_ROTATION = 180  # Add this constant

    def __init__(self) -> None:
        pass

    def read_image(self, image_path: str | Path) -> ImageType:
        """Read and convert image to BGR format.

        Args:
            image_path: Path to the image file

        Returns:
            ImageType: Image in BGR format
        """
        path = Path(image_path)
        with path.open("rb") as f:
            img_array = np.frombuffer(f.read(), dtype=np.uint8)
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError(f"Failed to read image at {path}")
            return image.astype(np.uint8)

    def remove_noise(self, image: ImageType) -> ImageType:
        """Remove noise while preserving edges.

        Args:
            image: Input image

        Returns:
            ImageType: Denoised image
        """
        result = cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)
        return result.astype(np.uint8)

    def sharpen_image(self, image: ImageType) -> ImageType:
        """Sharpen the image using unsharp masking.

        Args:
            image: Input image

        Returns:
            ImageType: Sharpened image
        """
        gaussian = cv2.GaussianBlur(image, (0, 0), 3.0)
        result = cv2.addWeighted(image, 1.5, gaussian, -0.5, 0)
        return result.astype(np.uint8)

    def detect_edges(self, image: ImageType) -> ImageType:
        """Detect edges in the image using Canny edge detection.

        Args:
            image: Input image

        Returns:
            ImageType: Edge map
        """
        gray = (
            cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if len(image.shape) == self._RGB_CHANNELS
            else image
        )
        result = cv2.Canny(gray, 50, 150)
        return result.astype(np.uint8)

    def correct_angle(self, image: ImageType) -> tuple[ImageType, float]:
        """Correct the angle of the image using Hough transform.

        Args:
            image: Input image

        Returns:
            Tuple[ImageType, float]: Rotated image and rotation angle
        """
        if image.dtype != np.uint8:
            image = np.asarray(image, dtype=np.uint8)

        edges = self.detect_edges(image)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)

        if lines is None:
            return image, 0.0

        # Collect all angles
        angles = []
        for _, theta in lines[:, 0]:
            angle = np.degrees(theta)
            # Convert angle to [-90, 90)
            if angle > self._ANGLE_THRESHOLD:
                angle -= 180
            angles.append(angle)

        if not angles:
            return image, 0.0

        median_angle = np.median(angles)

        # Only allow 0 or 180 degree rotation (landscape)
        snapped_angle = self._FULL_ROTATION if abs(median_angle) > self._ANGLE_THRESHOLD else 0
        if abs(snapped_angle) == self._FULL_ROTATION:
            snapped_angle = 0  # 180° rotation is the same as 0° for a rectangle

        if abs(snapped_angle) > 1:
            height, width = image.shape[:2]
            center = (width // 2, height // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, snapped_angle, 1.0)
            rotated = cv2.warpAffine(
                image,
                rotation_matrix,
                (width, height),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
            return rotated.astype(np.uint8), float(snapped_angle)
        return image, 0.0

    def adjust_contrast_brightness(
        self, image: ImageType, alpha: float = 1.2, beta: int = 10
    ) -> ImageType:
        """Adjust contrast and brightness of the image.

        Args:
            image: Input image
            alpha: Contrast control (1.0-3.0)
            beta: Brightness control (0-100)

        Returns:
            ImageType: Adjusted image
        """
        result = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
        return result.astype(np.uint8)

    def process_image(self, image: ImageType) -> ImageType:
        """Process the image through the pipeline.

        Args:
            image: Input image
            output_dir: Not used, kept for backward compatibility
            base_filename: Not used, kept for backward compatibility

        Returns:
            ImageType: Processed image
        """
        # Remove noise while preserving edges
        denoised = self.remove_noise(image)

        # Sharpen the image
        sharpened = self.sharpen_image(denoised)

        # Ensure correct type before passing to correct_angle
        sharpened_uint8 = np.asarray(sharpened, dtype=np.uint8)

        # Correct image orientation
        corrected, _ = self.correct_angle(sharpened_uint8)

        return corrected

    def preprocess(self, image_path: str | Path) -> ImageType:
        """Apply preprocessing steps optimized for card detection."""
        image = self.read_image(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        return gray_bgr.astype(np.uint8)
