"""
Usage:
> python cli.py --help

"""

# noqa: ANN201
import typer
from typing_extensions import Annotated

app = typer.Typer()


@app.command()
def hello(name: Annotated[str, typer.Argument(..., help="Your name")]) -> None:
    typer.echo(f"Hello, {name}")


if __name__ == "__main__":
    app()
