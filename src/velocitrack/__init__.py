try:
    from importlib.metadata import version

    __version__ = version("velocitrack")
except Exception:
    __version__ = "0.0.0"  # fallback for dev
