import base64
import logging
import re
from io import BytesIO
from typing import Literal, TypedDict, cast

import cv2
import numpy as np
from langchain_core.messages import HumanMessage  # type: ignore[import-not-found]
from langchain_core.output_parsers import StrOutputParser  # type: ignore[import-not-found]
from langchain_core.runnables import RunnableSequence  # type: ignore[import-not-found]
from langchain_ollama import ChatOllama  # type: ignore[import-not-found]
from numpy.typing import NDArray
from PIL import Image  # type: ignore[import-not-found]
from tenacity import retry, stop_after_attempt, wait_exponential  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)


class IDCardFields(TypedDict):
    """Extracted fields from ID card."""

    name: str | None
    birth_date: str | None
    issue_date: str | None
    gender: Literal["男", "女"] | None
    id_number: str | None
    father_name: str | None
    mother_name: str | None
    spouse_name: str | None
    military_service: str | None
    birth_place: str | None
    address: str | None


## gemma3:27b
## gemma3:12b
## llama3.2-vision:11b
## mistral-small3.2:24b
## qwen2.5vl:7b


class LLMFieldExtractor:
    """Extract fields from ID card using LLM."""

    _NAME_LENGTH = 3

    def __init__(
        self,
        base_url: str = "http://tw-05.access.glows.ai:25421",
        model: str = "mistral-small3.2:24b",
    ) -> None:
        self.llm = ChatOllama(
            base_url=base_url,
            model=model,
            temperature=0.1,  # Lower temperature for more consistent responses
            timeout=30,  # 30 second timeout
        )
        self.chain = self._create_chain()
        self.logger = logging.getLogger(__name__)

    def _create_chain(self) -> RunnableSequence:
        """Create the LangChain processing chain."""
        return self._create_prompt | self.llm | StrOutputParser()

    def _create_prompt(self, data: dict[str, str]) -> list[HumanMessage]:
        """Create a prompt with text and image.

        Args:
            data: Dictionary containing text prompt and image

        Returns:
            List of messages for the LLM
        """
        text = data["text"]
        image = data["image"]

        image_part = {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image}"}

        text_part = {"type": "text", "text": text}

        content_parts = [image_part, text_part]
        return [HumanMessage(content=content_parts)]

    def convert_to_base64(self, image: NDArray[np.uint8]) -> str:
        """Convert OpenCV image to base64 string.

        Args:
            image: OpenCV image in BGR format

        Returns:
            Base64 encoded image string
        """
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)

        buffered = BytesIO()
        pil_image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def _clean_text(self, text: str) -> str:
        """Clean text by removing special characters and extra spaces.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return text

        # Remove asterisks and extra spaces
        cleaned = text.strip()
        cleaned = cleaned.strip("*").strip()
        cleaned = cleaned.replace("**", "").replace("*", "")

        # Remove extra spaces
        cleaned = " ".join(cleaned.split())

        # Remove header/footer text
        if any(skip in cleaned for skip in ["以下是", "辨識", "希望", "中華民國"]):
            return ""

        return cleaned

    def _parse_id_card_text(self, text: str) -> dict[str, str | None]:
        """Parse unstructured text from ID card (both front and back)."""
        result = self._init_result_dict()
        address_parts: list[str] = []

        for text_line in text.split("\n"):
            line = self._clean_text(text_line)
            if not line:
                continue

            self._parse_front_fields(line, result)
            self._parse_back_fields(line, result, address_parts)

        if address_parts:
            result["address"] = " ".join(address_parts)
        return result

    def _init_result_dict(self) -> dict[str, str | None]:
        """Initialize empty result dictionary."""
        return {
            "name": None,
            "birth_date": None,
            "issue_date": None,
            "gender": None,
            "id_number": None,
            "father_name": None,
            "mother_name": None,
            "spouse_name": None,
            "military_service": None,
            "birth_place": None,
            "address": None,
        }

    def _parse_front_fields(self, line: str, result: dict[str, str | None]) -> None:
        """Parse front side ID card fields."""
        parsers = [
            self._parse_name,
            self._parse_gender,
            self._parse_birth_date,
            self._parse_issue_date,
            self._parse_id_number,
        ]
        for parser in parsers:
            parser(line, result)

    def _parse_name(self, line: str, result: dict[str, str | None]) -> None:
        if "姓名" in line:
            result["name"] = self._clean_text(line.split("姓名：")[1]) if "姓名：" in line else None

    def _parse_gender(self, line: str, result: dict[str, str | None]) -> None:
        if "性別" in line:
            gender_text = self._clean_text(line.split("性別：")[1]) if "性別：" in line else None
            if gender_text in ["男", "女"]:
                result["gender"] = cast('Literal["男", "女"]', gender_text)

    def _parse_birth_date(self, line: str, result: dict[str, str | None]) -> None:
        if "出生" in line and "：" in line:
            for prefix in ["出生：", "出生日期：", "出生年月：", "出生年月日："]:
                if prefix in line:
                    result["birth_date"] = self._clean_text(line.split(prefix)[1])
                    break

    def _parse_issue_date(self, line: str, result: dict[str, str | None]) -> None:
        if any(x in line for x in ["有效期限", "有效期間", "有效日期", "發證日期"]):
            result["issue_date"] = self._clean_text(
                line.split("：")[1].split("（")[0].split("(")[0]
            )

    def _parse_id_number(self, line: str, result: dict[str, str | None]) -> None:
        if "身分證字號" in line and "：" in line:
            result["id_number"] = self._clean_text(line.split("：")[1])
        else:
            id_match = re.search(r"[A-Z]\d{9}", line)
            if id_match:
                result["id_number"] = id_match.group(0)

    def _parse_back_fields(
        self, line: str, result: dict[str, str | None], address_parts: list[str]
    ) -> None:
        """Parse back side ID card fields."""
        # Father name
        if line.startswith(("父：", "父:")):
            result["father_name"] = self._clean_text(
                line.split("：", 1)[-1] if "：" in line else line.split(":", 1)[-1]
            )
        # Mother name
        elif line.startswith(("母：", "母:")):
            result["mother_name"] = self._clean_text(
                line.split("：", 1)[-1] if "：" in line else line.split(":", 1)[-1]
            )
        # Spouse name
        elif line.startswith(("配偶：", "配偶:")):
            result["spouse_name"] = self._clean_text(
                line.split("：", 1)[-1] if "：" in line else line.split(":", 1)[-1]
            )
        # Military service
        elif line.startswith(("役別：", "役別:")):
            value = self._clean_text(
                line.split("：", 1)[-1] if "：" in line else line.split(":", 1)[-1]
            )
            # If the value is "役別", treat it as "無"
            result["military_service"] = "無" if value == "役別" else value
        # Birth place
        elif line.startswith(("出生地：", "出生地:")):
            result["birth_place"] = self._clean_text(
                line.split("：", 1)[-1] if "：" in line else line.split(":", 1)[-1]
            )
        # Address (may be multi-line)
        elif line.startswith(("住址：", "住址:")) or address_parts:
            self._handle_address(line, address_parts)

    def _handle_address(self, line: str, address_parts: list[str]) -> None:
        """Handle address parsing."""
        if "住址" in line:
            parts = line.split("住址")
            if len(parts) > 1:
                address_parts.append(self._clean_text(parts[1].lstrip("：:").strip()))
        else:
            address_parts.append(self._clean_text(line))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))  # type: ignore[misc]
    def extract_fields(
        self, image: NDArray[np.uint8], side: Literal["front", "back"]
    ) -> IDCardFields:
        """Extract fields from ID card image using LLM."""
        image_b64 = self.convert_to_base64(image)

        if side == "front":
            prompt = """請辨識身分證正面的文字，並以下列格式回覆：
姓名：[姓名]
性別：[性別]
出生：[出生日期]
發證日期：[發證日期]
身分證字號：[身分證字號]"""
        else:
            prompt = """請辨識身分證背面的文字，並以下列格式回覆：
父：[父親姓名]
母：[母親姓名]
配偶：[配偶姓名]
役別：[役別]
出生地：[出生地]
住址：[住址] (住址有可能會有上下兩排)"""

        self.logger.info(f"Sending prompt to LLM for {side} side extraction")
        response = self.chain.invoke({"text": prompt, "image": image_b64})
        self.logger.info(f"LLM Response: {response}")

        # Parse the response
        parsed = self._parse_id_card_text(response)

        # Convert to IDCardFields type
        fields: IDCardFields = {
            "name": parsed["name"],
            "birth_date": parsed["birth_date"],
            "issue_date": parsed["issue_date"],
            "gender": cast('Literal["男", "女"] | None', parsed["gender"]),
            "id_number": parsed["id_number"],
            "father_name": parsed["father_name"],
            "mother_name": parsed["mother_name"],
            "spouse_name": parsed["spouse_name"],
            "military_service": parsed["military_service"],
            "birth_place": parsed["birth_place"],
            "address": parsed["address"],
        }

        return fields
