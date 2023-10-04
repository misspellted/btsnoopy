

"""
Parses a btsnoop file.

Usage: python main.py <btsnoop_file_path>
"""

from btsnoopy import BtSnoopFile
import sys

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(1)

  bsf, error = BtSnoopFile.read(sys.argv[1])

  if error:
    print(f"!!! Failed to read btsnoop file '{sys.argv[1]}': {error}")
  else:
    print(f">>> btsnoop file '{sys.argv[1]}' contains {len(bsf.packet_records)} record(s)")


# TODO: So many unit tests!

