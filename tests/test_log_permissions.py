import os
import stat
import tempfile
from pathlib import Path


def main():
    with tempfile.TemporaryDirectory(prefix="rae-log-") as directory:
        log = Path(directory) / "egress.log"
        log.write_text("synthetic-run-001 localhost\n")
        log.chmod(stat.S_IRUSR | stat.S_IWUSR)
        mode = stat.S_IMODE(log.stat().st_mode)
        assert mode == 0o600
        assert not mode & (stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
        assert log.read_text().startswith("synthetic-run-001")
    print("log access permission test: PASS")


if __name__ == "__main__":
    main()
