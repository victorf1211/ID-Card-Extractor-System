import datetime
import shutil
import traceback
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from idcard_extractor.backend.services.processor import IDCardProcessor

app = FastAPI()

# Define constants for directories
UPLOAD_DIR = Path("data/uploaded")
OUTPUT_DIR = Path("data/web_output")

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Add this function to handle file uploads
async def save_uploaded_file(file: UploadFile) -> Path:
    """
    Save the uploaded file to a temporary location and return the path.

    Args:
        file (UploadFile): The uploaded file object

    Returns:
        Path: Path to the saved file
    """
    # Generate unique filename using UUID and original extension
    original_extension = Path(file.filename or "").suffix
    unique_filename = f"{uuid.uuid4()}{original_extension}"
    file_path = UPLOAD_DIR / unique_filename

    # Save the file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path


@app.get("/", response_class=HTMLResponse)
async def main_page() -> HTMLResponse:
    return HTMLResponse(
        """
        <html>
            <body>
                <h2>ID Card Extractor - Upload</h2>
                <form action="/upload/" enctype="multipart/form-data" method="post">
                    <input name="file" type="file" accept="image/*">
                    <input type="submit" value="Upload">
                </form>
            </body>
        </html>
        """
    )


def _serialize_fields(fields: dict[str, Any]) -> dict[str, Any]:
    """Convert datetime objects to ISO strings for display."""
    return {
        k: (v.isoformat() if isinstance(v, datetime.datetime) else v) for k, v in fields.items()
    }


class UploadResponse(BaseModel):
    success: bool
    fields: dict[str, Any]
    csv_download_url: str | None = None
    error: str | None = None


@app.post("/upload/", response_model=UploadResponse, summary="上傳身分證圖片並擷取欄位")
async def upload_file(
    file: Annotated[UploadFile, File(...)],
    side: Annotated[str | None, Form()] = None,
) -> JSONResponse:
    try:
        # Save uploaded file
        file_path = await save_uploaded_file(file)

        # Process the image
        processor = IDCardProcessor(output_dir=str(OUTPUT_DIR))
        result = processor.process(file_path, export_csv=True, side=side)

        fields = result.get("fields", {})
        serialized_fields = _serialize_fields(dict(fields))

        tmp: Any = result.get("export_result", {})
        if not isinstance(tmp, dict):
            tmp = {}
        export_result: dict[str, Any] = tmp
        if export_result.get("success"):
            csv_path = export_result.get("file_path")
            csv_filename = Path(csv_path).name if csv_path else None
            return JSONResponse(
                content={
                    "success": True,
                    "fields": serialized_fields,
                    "csv_download_url": f"/download/{csv_filename}" if csv_filename else None,
                }
            )

        error_msg = export_result.get(
            "error", f"Unknown error occurred. export_result={export_result}"
        )
        return JSONResponse(
            content={
                "success": False,
                "fields": serialized_fields,
                "error": error_msg,
            },
            status_code=500,
        )

    except (OSError, ValueError, RuntimeError) as e:
        error_traceback = traceback.format_exc()
        return JSONResponse(
            content={
                "success": False,
                "error": str(e),
                "traceback": error_traceback,
            },
            status_code=500,
        )


@app.get("/download/{file}")
async def download_csv(file: str) -> Response:
    try:
        file_path = OUTPUT_DIR / file

        if not file_path.exists():
            return Response(content=f"File {file} not found at {file_path}", status_code=404)

        def read_file_bytes(path: Path) -> bytes:
            with path.open("rb") as f:
                return f.read()

        contents = await run_in_threadpool(read_file_bytes, file_path)

        return Response(
            content=contents,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={file}"},
        )
    except (OSError, ValueError) as e:
        return Response(content=f"Error: {e!s}", status_code=500)
