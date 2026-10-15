import multiprocessing
import os
import tempfile
import time
from pathlib import Path


def writer(path):
    Path(path, "synthetic-secret.txt").write_text("canary-only")
    time.sleep(30)


def main():
    with tempfile.TemporaryDirectory(prefix="rae-ephemeral-") as directory:
        process = multiprocessing.Process(target=writer, args=(directory,))
        process.start()
        process.join(timeout=2)
        process.terminate()
        process.join(timeout=5)
        assert process.exitcode is not None
        assert Path(directory, "synthetic-secret.txt").exists()
    assert not os.path.exists(directory)
    print("ephemeral interruption cleanup test: PASS")


if __name__ == "__main__":
    main()
