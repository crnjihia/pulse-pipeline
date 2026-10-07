# pulse/__main__.py
"""Entry point for `python -m pulse`.
It forwards to the project's CLI implementation.
"""
from cli import main

if __name__ == "__main__":
    main()
