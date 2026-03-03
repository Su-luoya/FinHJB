__version__ = "0.1.0"


def hello(name: str = "FinHJB") -> None:
    """Print a hello message using rich.

    Args:
        name: Name to greet
    """
    from rich.console import Console

    Console().print(f"[bold green]Hello from {name}![/bold green]")


__all__ = ["__version__", "hello"]
