import argparse
import logging
from pathlib import Path

import cv2
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from idcard_extractor.backend.services.processor import IDCardProcessor

# Set up rich console for better output
console = Console()

# Configure logging with rich
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)


def process_single_image(image_path: Path, processor: IDCardProcessor, debug: bool = False) -> bool:
    """Process a single image file."""
    try:
        result = processor.process(image_path=str(image_path), export_csv=True)
    except (ValueError, OSError, cv2.error) as e:
        logger.error(f"Error processing {image_path.name}: {e}")
        return False
    else:
        # Print extracted fields
        console.print(f"\n[bold blue]Results for {image_path.name}:[/]")
        console.print("─" * 50)

        for field, value in result["fields"].items():
            console.print(f"[green]{field}:[/] {value}")

        if debug:
            debug_dir = Path(image_path).parent / "debug" / image_path.stem
            debug_dir.mkdir(parents=True, exist_ok=True)

            debug_images = {
                "preprocessed.jpg": result["preprocessed_image"],
                "card_region.jpg": result["card_region"],
                "standardized.jpg": result["standardized_image"],
            }

            for name, img in debug_images.items():
                cv2.imwrite(str(debug_dir / name), img)

            console.print(f"[blue]Debug images saved to:[/] {debug_dir}")

        return True


def process_batch(
    input_dir: Path, processor: IDCardProcessor, debug: bool = False
) -> tuple[int, int]:
    """Process all images in a directory.

    Args:
        input_dir: Directory containing images to process
        processor: Initialized ID card processor
        debug: Whether to save debug images

    Returns:
        tuple: (number of successful processes, total number of files)
    """
    # Get all image files
    image_files = (
        list(input_dir.glob("*.jpg"))
        + list(input_dir.glob("*.jpeg"))
        + list(input_dir.glob("*.png"))
    )

    if not image_files:
        console.print("[yellow]No image files found in the input directory[/]")
        return 0, 0

    successful = 0
    total = len(image_files)

    # Process files with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Processing images...", total=total)

        for image_file in image_files:
            if process_single_image(image_file, processor, debug):
                successful += 1
            progress.update(task, advance=1)

    return successful, total


def main() -> None:
    parser = argparse.ArgumentParser(description="ID Card Extractor CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", type=Path, help="Path to a single image file")
    group.add_argument(
        "--input-dir", type=Path, help="Directory containing images for batch processing"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/output"), help="Directory to save results"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode (save intermediate images)"
    )
    parser.add_argument(
        "--side", type=str, choices=["front", "back"], help="Specify side: front or back"
    )
    args = parser.parse_args()

    processor = IDCardProcessor(output_dir=args.output_dir)

    if args.image:
        processor.process(args.image, export_csv=True, side=args.side)
    else:
        # Collect all jpg and png images in the input directory
        image_files = list(args.input_dir.glob("*.jpg")) + list(args.input_dir.glob("*.png"))
        if not image_files:
            console.print(f"[red]No images found in {args.input_dir}[/]")
            return
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Processing images...", total=len(image_files))
            for image_path in image_files:
                process_single_image(image_path, processor, debug=args.debug)
                progress.update(task, advance=1)
        console.print(f"[green]Batch processing complete! Results saved to {args.output_dir}[/]")


if __name__ == "__main__":
    main()
