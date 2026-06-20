"""Compatibility entrypoint for the PostgreSQL-backed web dashboard."""

from fake_system.web.app import serve

if __name__ == "__main__":
    serve()
