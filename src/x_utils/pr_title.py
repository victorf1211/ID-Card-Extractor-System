import typer
from gitmojify.mojify import gitmojify


def validate_pr_title(pr_title: str) -> None:
    """在 commit message 開頭添加 gitmoji

    CLI Examples:
        python3 src/x_utils/_pr_title.py "feat: add new feature"
    """
    typer.echo(gitmojify(pr_title))


if __name__ == "__main__":
    typer.run(validate_pr_title)
