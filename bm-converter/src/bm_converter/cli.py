import argparse
import sys
from pathlib import Path

from .converter import convert_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Model_*.txt planetary models to AxiSEM .bm format"
    )
    parser.add_argument("input", type=Path, nargs="+", help="Input Model_*.txt file(s)")
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: same as input file)",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Model name written into the .bm header (default: input filename stem). "
             "Ignored when converting multiple files.",
    )
    parser.add_argument(
        "--planet-radius",
        type=float,
        default=None,
        metavar="KM",
        help="Planet radius in km (default: inferred from max depth in the file)",
    )
    parser.add_argument("--anelastic", action="store_true", help="Mark model as anelastic")
    parser.add_argument("--anisotropic", action="store_true", help="Mark model as anisotropic")

    args = parser.parse_args()

    if args.name and len(args.input) > 1:
        print("Warning: --name is ignored when converting multiple files.", file=sys.stderr)

    for input_path in args.input:
        if not input_path.is_file():
            print(f"Error: {input_path} not found", file=sys.stderr)
            sys.exit(1)

        out_dir = args.output_dir if args.output_dir is not None else input_path.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        output_path = out_dir / (input_path.stem + ".bm")

        name = args.name if (args.name and len(args.input) == 1) else input_path.stem

        convert_file(
            input_path=input_path,
            output_path=output_path,
            name=name,
            planet_radius_km=args.planet_radius,
            anelastic=args.anelastic,
            anisotropic=args.anisotropic,
        )
        print(f"{input_path} -> {output_path}")


if __name__ == "__main__":
    main()
