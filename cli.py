"""
Usage:
> python cli.py --help

"""

# noqa: ANN201
import typer

app = typer.Typer()


@app.command()
def hello(name: str = typer.Argument(..., help="Your name")) -> None:
    typer.echo(f"Hello, {name}")


if __name__ == "__main__":
    app()
