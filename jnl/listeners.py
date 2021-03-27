import binascii
import os
import re

import xattr

import jnl.system


class NopListener(object):
    def __init__(self, context: "Context"):
        self.context = context
        self.state = {}

    def on_entry(self, entry: "Entry") -> None:
        pass

    def on_pre_scan(self) -> None:
        pass

    def on_post_scan(self) -> None:
        pass


class SetsOpenWith(NopListener):
    def __init__(self, context: "Context"):
        super().__init__(context)

    """The xattr controlling the "Open With" functionality is unfortunately binary.
    To use a different application, use `xattr -px`

    or with `-px`:

        $ xattr -px com.apple.LaunchServices.OpenWith $FILE
        62 70 6C 69 73 74 30 30 D3 01 02 03 04 05 06 57
        [...]
        00 00 00 00 00 6F
    """

    OPEN_WITH_ATTR_HEX = re.sub(
        r"\s*",
        "",
        """
        62 70 6C 69 73 74 30 30 D3 01 02 03 04 05 06 57
        76 65 72 73 69 6F 6E 54 70 61 74 68 5F 10 10 62
        75 6E 64 6C 65 69 64 65 6E 74 69 66 69 65 72 10
        00 5F 10 1D 2F 41 70 70 6C 69 63 61 74 69 6F 6E
        73 2F 46 6F 6C 64 69 6E 67 54 65 78 74 2E 61 70
        70 5F 10 1B 63 6F 6D 2E 66 6F 6C 64 69 6E 67 74
        65 78 74 2E 46 6F 6C 64 69 6E 67 54 65 78 74 08
        0F 17 1C 2F 31 51 00 00 00 00 00 00 01 01 00 00
        00 00 00 00 00 07 00 00 00 00 00 00 00 00 00 00
        00 00 00 00 00 6F
    """,
        flags=re.M,
    )

    OPEN_WITH_ATTR = binascii.unhexlify(OPEN_WITH_ATTR_HEX)

    def on_entry(self, entry: "Entry") -> None:
        if not entry.has_tag("ft", None):
            return

        return xattr.setxattr(
            entry.file_path(),
            "com.apple.LaunchServices.OpenWith",
            SetsOpenWith.OPEN_WITH_ATTR,
        )


class Symlinker(NopListener):
    def on_entry(self, entry: "Entry") -> None:
        if self.state.get("yyyymmdd") is None:
            self.state["yyyymmdd"] = jnl.system.yyyymmdd()
        tags = [t for t in entry.tags if t.name == "quick" and t.value is not None]
        for tag in tags:
            val = tag.value
            parts = val.split("/")
            dir_parts = parts[:-1]
            past = parts[-1]
            filename_part = "%s.%s" % (past, entry.file_extension())
            into_dir = self.context.database.path("quick", *dir_parts)
            symlink = os.path.join(into_dir, filename_part)
            if jnl.system.exists(symlink):
                existing = jnl.system.readlink(symlink)
                if existing == entry.file_path():
                    # job already done
                    continue
                else:
                    raise ValueError(
                        "@quick(%s) owned by %s, so %s can't take it"
                        % (val, existing, entry.file_path())
                    )
            jnl.system.symlink(entry.file_path(), symlink)


class PreScanQuickCleaner(NopListener):
    def on_pre_scan(self) -> None:
        path = self.context.database.path("quick")
        print(("Scanning %s" % path))
        if jnl.system.exists(path):
            jnl.system.rmtree(path)
