#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import argparse

from classes.SyntheticReaders import Reader

r = Reader()
rp = r.ReaderPanels()
rs = r.Readers()

new_reader_panel = rp.create_reader_panel("TestPanel", 10, r.default_genres, r.default_tastes, r.default_genders, r.default_ages, r.default_faker_locale)

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--reader_panel_name', type=str, default='TestPanel')
    argparser.add_argument('--number_of_readers', '-n', type=int, default=10)
    argparser.add_argument('--default_genres', type=list, default=r.default_genres)
    argparser.add_argument('--default_tastes', type=list, default=r.default_tastes)
    argparser.add_argument('--default_genders', type=list, default=r.default_genders)
    argparser.add_argument('--default_ages', type=list, default=r.default_ages)
    argparser.add_argument('--default_faker_locale', type=str, default=r.default_faker_locale)
    args = argparser.parse_args()
    print(args)
    new_reader_panel = rp.create_reader_panel(args.reader_panel_name, args.number_of_readers, args.default_genres, args.default_tastes, args.default_genders, args.default_ages, args.default_faker_locale)
    reader_panel_with_bios = rp.add_LLM_bios_to_reader_panel_rows(new_reader_panel)
    print(reader_panel_with_bios)
    reader_panel_with_bios.to_csv(f'resources/reader_panels/{args.reader_panel_name}.csv')
