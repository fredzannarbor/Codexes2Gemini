#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import argparse
import os
import subprocess
import traceback


def process_bookjson_files(directory, coverfiles, max=2, headless=False):
    """Process .json files in a directory to generate .sla files."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    if not os.path.exists(coverfiles):
        os.makedirs(coverfiles)
    # Loop over each file in the directory

    count = 0
    for filename in os.listdir(directory):
        if count >= max:
            break
        if filename.endswith('.json'):
            bookjsonfilepath = os.path.join(directory, filename)
            basejsonname = filename[:-4]
            sla_filepath = os.path.join(coverfiles, basejsonname + 'sla')

            try:
                print(f'reading {filename}'.format(filename=filename))
                print(f'writing sla_filepath {sla_filepath}')
                if headless:
                    command = (
                        f'/Applications/Scribus15xNightly.app/Contents/MacOS/Scribus -g -py '
                        f'classes/Codexes/PartsOfTheBook/Covers/lsicover.py '
                        f'--headless -i="{bookjsonfilepath}" --outputfilepath="{sla_filepath}"'
                    )
                else:
                    print("exiting, headless is False")
                subprocess.run(command, shell=True)
                count += 1

            except Exception as e:
                print(f'failed to create {sla_filepath}')
                traceback.print_exc()

    print("Processing complete")
    print(f"input was: {directory}")
    print(f"output was: {coverfiles}")
    print(f"files processed was: {max}")


def main():
    parser = argparse.ArgumentParser(description="Process book JSON files to generate SLA files.")
    parser.add_argument('-i', '--input', type=str, required=True, help="Input directory containing book.json files")
    parser.add_argument('-o', '--output', type=str, required=True, help="Output directory for cover files")
    parser.add_argument('--max-files', type=int, required=True, help="Maximum number of files to process", default=2)
    parser.add_argument('--headless', dest='headless', action='store_true', help='Run in headless mode')

    args = parser.parse_args()
    print("--- Beginning MultipleCoverBuilder ---")
    print("Processing book JSON files to generate SLA")
    print(f"input directory: {args.input}")
    print(f"output directory: {args.output}")

    process_bookjson_files(args.input, args.output, args.max_files, args.headless)


if __name__ == "__main__":
    # accept input and output *directories*
    main()
