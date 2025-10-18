import hashlib

def hash_url(url: str) -> str:
	"""Return a hex hash for a URL to use as filename base."""
	h = hashlib.sha256(url.encode("utf-8")).hexdigest()
	# keep filename reasonably short
	return h