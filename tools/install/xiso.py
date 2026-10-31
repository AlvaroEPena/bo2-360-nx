"""Reads Xbox 360 disc images (.iso): checks what is on them and extracts them.

An Xbox 360 game disc stores its files in XDVDFS, the Xbox's own file system. The game's partition starts at a fixed
offset that depends on the disc format (XGD1, XGD2 or XGD3), or at 0 for an image already trimmed to the game
partition. Inside it, sector 32 holds the volume descriptor: the magic "MICROSOFT*XBOX*MEDIA", then the root
directory's sector and size. A directory is a binary tree of entries, each with the offsets (in 4-byte words) of its
left and right neighbours, the file's first sector and size, its attributes and its name.

The reader below needs nothing but Python. It extracts only the files the chosen modes need, and it also lists an
image's root folder, to tell a Black Ops II disc from any other image without extracting anything.
"""
import os
import struct

SECTOR = 2048
MAGIC = b"MICROSOFT*XBOX*MEDIA"
# Where the game partition starts: a trimmed image (0), XGD3, XGD2 and XGD1 discs.
PARTITION_OFFSETS = (0, 0x2080000, 0xFD90000, 0x18300000)
ATTRIBUTE_DIRECTORY = 0x10
EMPTY = 0xFFFF


class XisoError(Exception):
    pass


class Xiso:
    """One disc image, opened read-only."""

    def __init__(self, path):
        self.path = path
        self.f = open(path, "rb")
        self.size = os.fstat(self.f.fileno()).st_size
        self.base = None
        for offset in PARTITION_OFFSETS:
            if offset + 33 * SECTOR > self.size:
                continue
            self.f.seek(offset + 32 * SECTOR)
            head = self.f.read(SECTOR)
            if head[:20] == MAGIC and head[SECTOR - 20:] == MAGIC:
                self.base = offset
                self.root_sector, self.root_size = struct.unpack_from("<II", head, 20)
                break
        if self.base is None:
            self.f.close()
            raise XisoError(f"{path} is not an Xbox disc image")

    def close(self):
        self.f.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _read(self, sector, size):
        self.f.seek(self.base + sector * SECTOR)
        data = self.f.read(size)
        if len(data) != size:
            raise XisoError(f"{self.path} ends early: is the image complete?")
        return data

    def directory(self, sector, size):
        """The entries of one directory: (name, is_directory, first sector, size)."""
        if size == 0:
            return []
        table = self._read(sector, size)
        found, pending, seen = [], [0], set()
        while pending:
            offset = pending.pop()
            if offset in seen or offset + 14 > len(table):
                continue
            seen.add(offset)
            left, right, start, length, attributes, name_length = struct.unpack_from("<HHIIBB", table, offset)
            if left == EMPTY and right == EMPTY and start == 0xFFFFFFFF:
                continue  # sector padding
            name = table[offset + 14:offset + 14 + name_length].decode("latin-1")
            if name:
                found.append((name, bool(attributes & ATTRIBUTE_DIRECTORY), start, length))
            for link in (left, right):
                if link not in (0, EMPTY):
                    pending.append(link * 4)
        return sorted(found, key=lambda e: e[0].lower())

    def root(self):
        return self.directory(self.root_sector, self.root_size)

    def walk(self, sector=None, size=None, prefix=""):
        """Every file in the image as (relative path, first sector, size)."""
        if sector is None:
            sector, size = self.root_sector, self.root_size
        for name, is_dir, start, length in self.directory(sector, size):
            rel = prefix + name
            if is_dir:
                yield from self.walk(start, length, rel + "/")
            else:
                yield rel, start, length

    def extract(self, out, skip=lambda rel: False, progress=None):
        """Copies the files into out; skip(relative path) leaves a file out. Files already there with the right size
        are kept, so an interrupted extraction carries on."""
        files = [f for f in self.walk() if not skip(f[0])]
        total = sum(f[2] for f in files) or 1
        done = 0
        for rel, start, length in files:
            dst = os.path.join(out, *rel.split("/"))
            if not (os.path.isfile(dst) and os.path.getsize(dst) == length):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                self.f.seek(self.base + start * SECTOR)
                remaining = length
                with open(dst + ".part", "wb") as w:
                    while remaining:
                        chunk = self.f.read(min(remaining, 1 << 22))
                        if not chunk:
                            raise XisoError(f"{self.path} ends early while reading {rel}")
                        w.write(chunk)
                        remaining -= len(chunk)
                os.replace(dst + ".part", dst)
            done += length
            if progress:
                progress(done, total, rel)
        return len(files)


def is_xbox_image(path):
    try:
        with Xiso(path):
            return True
    except (XisoError, OSError):
        return False


def root_names(path):
    """The names in the image's root folder, lower case (an empty set for an image that cannot be read)."""
    try:
        with Xiso(path) as x:
            return {name.lower() for name, _, _, _ in x.root()}
    except (XisoError, OSError):
        return set()
