import argparse
import fst.au.daemon


def main():
    parser = argparse.ArgumentParser(
        description=("Watches a template directory for changes and "
                     "modifies it's instances in the same way when one occurs.")
    )
    parser.add_argument("db", help="Path to fst database.",
			nargs='?',
			default=fst.db.DB_PATH)
    args = parser.parse_args()
    fst.au.daemon.start(args.db)


if __name__ == "__main__":
    main()
