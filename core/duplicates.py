"""Duplicate file detection using size grouping and SHA-256 content hashing."""
import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional
from core.models import FileItem


def compute_sha256(path: Path, chunk_size: int = 65536) -> Optional[str]:
    """Computes SHA-256 checksum of a file in streaming chunks."""
    hasher = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, PermissionError):
        return None


def find_duplicates(items: List[FileItem]) -> Dict[str, List[FileItem]]:
    """Identifies duplicate files among the given FileItems.
    
    Returns a dictionary mapping hash -> list of duplicate FileItems (only for groups with >1 file).
    """
    # 1. Group by file size first (fast pre-filter)
    size_map = defaultdict(list)
    for item in items:
        if item.size_bytes > 0:  # Skip 0-byte files or group them separately
            size_map[item.size_bytes].append(item)

    # 2. For items with identical sizes, compute hash
    hash_map = defaultdict(list)
    for size, group in size_map.items():
        if len(group) < 2:
            continue
        for item in group:
            digest = compute_sha256(item.original_path)
            if digest:
                hash_map[digest].append(item)

    # Filter to only groups with 2 or more files
    duplicates = {digest: group for digest, group in hash_map.items() if len(group) > 1}
    return duplicates
