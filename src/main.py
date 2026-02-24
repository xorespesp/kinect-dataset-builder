import sys
import logging
import argparse
from pathlib import Path

from builder_impl_rgb import RGBDatasetBuilder

def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] <%(name)s.%(funcName)s:%(lineno)d> %(message)s'
    )

def main() -> None:
    parser = argparse.ArgumentParser(description="Kinect Dataset Builder")
    parser.add_argument('input_mkv', type=Path, help="Path to the input MKV file")
    parser.add_argument('-o', '--output', type=Path, default=None, help="Optional output directory path")
    
    args = parser.parse_args()
    
    setup_logging()
    
    builder = RGBDatasetBuilder(output_dir=args.output)
    
    try:
        builder.process(args.input_mkv)
    except KeyboardInterrupt:
        logging.info("Process interrupted by user.")
    except Exception as e:
        logging.error("Dataset building process failed.", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()