import subprocess
import sys


def main():
    try:
        subprocess.run(
            [sys.executable, "-c", "import time; time.sleep(5)"],
            timeout=1,
            capture_output=True,
            check=True,
        )
    except subprocess.TimeoutExpired:
        pass
    else:
        raise AssertionError("runtime limit was not enforced")

    memory = subprocess.run(
        [
            sys.executable,
            "-c",
            "import resource; resource.setrlimit(resource.RLIMIT_AS, (64*1024*1024, 64*1024*1024)); bytearray(128*1024*1024)",
        ],
        capture_output=True,
    )
    assert memory.returncode != 0
    print("resource boundary tests: PASS")


if __name__ == "__main__":
    main()
