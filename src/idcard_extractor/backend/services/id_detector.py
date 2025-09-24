import logging
from collections.abc import Callable

import cv2
import numpy as np
from numpy.typing import NDArray

from .llm_extractor import LLMFieldExtractor

# Type aliases
ImageType = NDArray[np.uint8]
ContourType = list[list[int]]
ThresholdFunction = Callable[[ImageType], ImageType]


class IDCardDetector:
    """Detector for Taiwan ID cards."""

    # Standard Taiwan ID card aspect ratio (8.55 cm × 5.4 cm)
    _STANDARD_ASPECT_RATIO = 8.55 / 5.4  # width/height ratio
    _STANDARD_WIDTH = 1200
    _STANDARD_HEIGHT = int(_STANDARD_WIDTH / _STANDARD_ASPECT_RATIO)
    _MIN_CONTOUR_AREA = 1000  # pixels²
    _FRONT_SIDE_DENSITY_THRESHOLD = 0.3  # ratio of dark pixels
    _RECTANGLE_POINTS = 4  # number of points in a rectangle
    _ASPECT_RATIO_TOLERANCE = 0.4  # 40% tolerance
    _GRAY_THRESHOLD = 127  # threshold for dark/light pixels
    _PHOTO_DENSITY_THRESHOLD = 0.15  # Adjusted for better photo detection
    _MIN_TEXT_LINES = 2  # Minimum text lines to detect
    _FLAG_REGION_WIDTH = 0.15  # Width of flag region as proportion of card width
    _FLAG_REGION_HEIGHT = 0.2  # Height of flag region as proportion of card height
    _PHOTO_STD_THRESHOLD = 40  # Standard deviation threshold for photo detection
    _FLAG_STD_THRESHOLD = 30  # Standard deviation threshold for flag detection
    _PHOTO_STDDEV_THRESHOLD = 25

    def __init__(self) -> None:
        """Initialize the detector."""
        self.llm = LLMFieldExtractor()  # Add LLM initialization

    def detect_card_region(self, image: ImageType) -> tuple[ImageType, ContourType]:
        """Detect ID card region in the image.

        Args:
            image: Input image in BGR format

        Returns:
            tuple: (Cropped image, Contour points of the detected card)
        """
        # Convert to grayscale and enhance contrast
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        # Adaptive thresholding after histogram equalization
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 15
        )
        # Remove image border
        thresh[:5, :] = 0
        thresh[-5:, :] = 0
        thresh[:, :5] = 0
        thresh[:, -5:] = 0
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            raise ValueError("No ID card detected in the image")

        # Visualize all large contours for debugging
        debug_all = image.copy()
        for c in contours:
            if cv2.contourArea(c) > self._MIN_CONTOUR_AREA:
                cv2.drawContours(debug_all, [c], -1, (0, 255, 0), 2)
        # Sort contours by area
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        # Use the largest contour directly
        if len(contours) > 0:
            contour = contours[0]
            rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rect)
            box = box.astype(int)

            debug_img = image.copy()
            cv2.drawContours(debug_img, [box], -1, (0, 255, 0), 3)

            points = box.astype(np.float32)
            result = self._four_point_transform(image, points)
            if result.shape[1] < result.shape[0]:
                result = cv2.rotate(result, cv2.ROTATE_90_CLOCKWISE).astype(np.uint8)
            return result, [[int(x[0]), int(x[1])] for x in points]

        raise ValueError("No ID card detected in the image")

    def standardize_image(self, image: ImageType) -> ImageType:
        """Standardize the image size and orientation.

        Args:
            image: Input image

        Returns:
            NDArray: Standardized image
        """
        result = cv2.resize(image, (self._STANDARD_WIDTH, self._STANDARD_HEIGHT))
        return result.astype(np.uint8)

    def _order_points(self, pts: NDArray[np.float32]) -> NDArray[np.float32]:
        """Order points in clockwise order (top-left, top-right, bottom-right, bottom-left)."""
        rect = np.zeros((4, 2), dtype=np.float32)

        # Top-left will have smallest sum
        # Bottom-right will have largest sum
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        # Top-right will have smallest difference
        # Bottom-left will have largest difference
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        return rect

    def _four_point_transform(self, image: ImageType, pts: NDArray[np.float32]) -> ImageType:
        """Apply perspective transform.

        Args:
            image: Input image
            pts: Four points in float32 format

        Returns:
            ImageType: Transformed image
        """
        rect = self._order_points(pts)

        # Compute width of new image
        width_a = np.sqrt(((rect[2][0] - rect[3][0]) ** 2) + ((rect[2][1] - rect[3][1]) ** 2))
        width_b = np.sqrt(((rect[1][0] - rect[0][0]) ** 2) + ((rect[1][1] - rect[0][1]) ** 2))
        max_width = max(int(width_a), int(width_b))

        # Compute height of new image
        height_a = np.sqrt(((rect[1][0] - rect[2][0]) ** 2) + ((rect[1][1] - rect[2][1]) ** 2))
        height_b = np.sqrt(((rect[0][0] - rect[3][0]) ** 2) + ((rect[0][1] - rect[3][1]) ** 2))
        max_height = max(int(height_a), int(height_b))

        # Create destination points
        dst = np.array(
            [[0, 0], [max_width - 1, 0], [max_width - 1, max_height - 1], [0, max_height - 1]],
            dtype=np.float32,
        )

        # Calculate perspective transform matrix and apply it
        transform_matrix = cv2.getPerspectiveTransform(rect, dst)
        result = cv2.warpPerspective(image, transform_matrix, (max_width, max_height))
        return result.astype(np.uint8)
