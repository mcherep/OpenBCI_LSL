import argparse
from lib.streamerlsl import StreamerLSL


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=str, required=True)
    parser.add_argument('--gain', type=int, default=24)
    parser.add_argument('--daisy', action="store_true", required=False)
    args = parser.parse_args()

    lsl = StreamerLSL(args.port, args.gain, args.daisy)
    lsl.create_lsl()
    lsl.begin()


if __name__ == "__main__":
    main()
