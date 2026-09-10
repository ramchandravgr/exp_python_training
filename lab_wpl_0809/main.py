from src.pipeline import run_pipeline


def main():
    print("Starting weather pipeline...")
    run_pipeline()
    print("Done! Check the reports/ folder for output files.")


if __name__ == "__main__":
    main()
