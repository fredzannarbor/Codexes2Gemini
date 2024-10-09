class BulkProcessPDFs:
    '''
    Constructor for BookPublisherPDFProcess

    Attributes:
        pdf_directory,  # directory of pdfs to be processed
        output_dir,  # output directory
        list2string,  # convert list of strings to string
        cumulative_file_name,  # name of cumulative file
        page_limit,  # stop processing after this many pages
        working_dir,  # directory for working files
        profiling,  # print profiling
        payservices,  # use paid services
        engine,  # ocr engine to use
        run_recursive,  # run recursively
        single_file_path,  # single file path
        run_page_by_page,  # run page by page
        ai_metadata,  # run ai_metadata
        create_interior_postscript,  # create interior postscript
        mode,  # mode
        batch_limit,  # batch limit
        production_specs_filepath,  # production specs filepath
        add_to_final,  # add to final
        skip_llama_entirely  # skip llama entirely
    '''

    def __init__(self, pdf_directory='working', output_dir="output", list2string=False,
                 cumulative_file_name="cumulative_test", page_limit=10, working_dir="working",
                 profiling=False, payservices=True, model="gpt-3.5-turbo", run_recursive=True,
                 single_file_path="/dev/null", run_page_by_page=False, ai_metadata=True,
                 create_interior_postscript=False, mode="produce", batch_limit=1,
                 production_specs_filepath="working/traffic_cop/current_specs.csv", add_to_final=True,
                 skip_llama_entirely=False, filecount=0, filelist=[], successcount=0, failcount=0, flags="ADEPT"):
        self.pdf_directory = pdf_directory
        self.output_dir = output_dir
        self.list2string = list2string
        self.cumulative_file_name = cumulative_file_name
        self.page_limit = page_limit
        self.working_dir = working_dir
        self.profiling = profiling
        self.payservices = payservices
        self.model = model
        self.run_recursive = run_recursive
        self.single_file_path = single_file_path
        self.run_page_by_page = run_page_by_page
        self.ai_metadata = ai_metadata
        self.create_interior_postscript = create_interior_postscript
        self.mode = mode
        self.batch_limit = batch_limit
        self.production_specs_filepath = production_specs_filepath
        self.add_to_final = add_to_final
        self.skip_llama_entirely = skip_llama_entirely
        self.filecount = filecount
        self.filelist = filelist
        self.successcount = successcount
        self.failcount = failcount
        self.target_search_path = ""
        self.flags = flags

    def create_attribute(self, name, value):
        setattr(self, name, value)

    def replace_attribute(self, name, value):
        setattr(self, name, value)

    def update_attribute(self, name, value):
        setattr(self, name, value)

    def delete_attribute(self, name):
        delattr(self, name)

    # reset all attributes to default
    def reset_attributes(self):
        self.__init__()

    # delete all attributes
    def delete_all_attributes(self):
        for attr in dir(self):
            delattr(self, attr)

    # set selected attributes to match custom dictionary listing them and their values
    def set_attributes(self, custom_dict):
        for key, value in custom_dict.items():
            setattr(self, key, value)

    def get_all_attributes(self):
        return self.__dict__

    # get selected attributes and their values as a dictionary
    def get_selected_attributes(self, custom_dict):
        for key, value in custom_dict.items():
            setattr(self, key, value)

    def bulkprocesshandler(bp):

        if single_file_path != '/dev/null':
            print('single file path is ' + single_file_path)
            target_search_path = single_file_path
        else:
            extension = "*.pdf"
            print(f"pdf_directory is {bp.pdf_directory}")
            target_search_path = bp.pdf_directory  # os.path.join(bp.pdf_directory,
        print('target_search_path', bp.target_search_path)
        print('production_specs_filepath', bp.production_specs_filepath)
        cumulative_df = pd.DataFrame()
        specs_input_df = pd.DataFrame()
        specs_add_row_df = pd.DataFrame()

        if bp.mode == "assess":
            bp.create_interior_postscript = False
            bp.run_recursive = False
            bp.ai_metadata = False
            bp.payservices = False
            bp.run_page_by_page = False
            bp.single_file_path = None
            bp.profiling = False
            bp.page_limit = 10
            print("assessing candidates only")
            bp.production_specs_df = None
            bp.skip_llama_entirely = True

        elif bp.mode == "produce":
            bp.create_interior_postscript = False  # True
            bp.run_recursive = True
            bp.ai_metadata = True
            bp.payservices = True
            bp.single_file_path = None
            bp.profiling = False
            bp.text2images_generate_prompts = True
            bp.text2images_generate_images = True
            bp.page_limit = 1200
            bp.skip_llama_entirely = False

            try:
                # production_specs_df = pd.read_csv(production_specs_filepath)
                production_specs_df = pd.read_csv(bp.production_specs_filepath, encoding='latin1')
                print(f"production specs found at {bp.production_specs_filepath}")
                print(f"first 5 rows are: {production_specs_df.head()}")
                selected_for_production = production_specs_df['select'].sum()
                infomessage = f"{selected_for_production} files in production specs file are ready for production"
                st.info(infomessage)  # production_specs_df = pd.DataFrame()
            except Exception as e:
                print('error reading production specs file', e)
                pass

            selected_for_production = production_specs_df['select'].sum()
            infomessage = f"{selected_for_production} files in production specs file are ready for production"
            print(infomessage)
        timestamped_filename = datetime.datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")

        checkresults = pd.DataFrame()
        print("looping over pdfs at path: ", target_search_path)
        st.write("looping over pdfs at path: ", target_search_path)
        success, errors = 0, 0
        filecount = 0
        config_file_count = 0
        results = []

        config = {}
        # endregion

        number_of_files = len(
            glob.glob(target_search_path))
        print(number_of_files, "files found in directory", target_search_path)

        st.write(f"number of files in directory {target_search_path} is {number_of_files}")
        if number_of_files == 0:
            print(f"no files found in directory {target_search_path}")
            exit()
        if number_of_files >= 101:
            print(f"More than 100 files found in directory {target_search_path}")
            print(f"do you want to continue? (y/n)")
            # answer = input()
            answer = "Yes"
            answer2 = st.checkbox("Yes", value=True, key=None, help=None)

            if answer == "Yes" or answer == "yes" or answer == "y" or answer == "Y" or answer2 == True:
                pass
            else:
                print("exiting")
                exit()

        for filename in glob.glob(target_search_path):  # loop over files in directory

            print("****** filename is ", filename, "*********")
            pathfile = Path(filename)
            shortname = pathfile.with_suffix("")  # check for config file
            config, config_file_count = check_for_config_file(config, config_file_count, shortname)
            # request analysis of current document
            try:
                # st.info('before results')
                sp = Handler4SinglePDF(bp, filename)
                results = ADEPTize_single_pdf(sp)
            except Exception as e:
                print('error processing pdf', e)
                results = []
            try:
                print('results', results)

                # df_row = pd.DataFrame.from_dict(results[1])  # metadatas
                df_row = results[1]
                # print(df_row, type(df_row))
                df_row['success'] = True
                df_row.to_json(output_dir + "/dfrow.json", orient="records")
                # exit()# st.write('df_row')

                # st.dataframe(df_row.T, width=1000, height=1000)
            except Exception as e:
                df_row = pd.DataFrame()
                df_row['success'] = False
            print('df_row', df_row)

            try:
                titlestring = df_row['title'].values[0]
                subtitlestring = df_row['subtitle'].values[0]
                authorstring = df_row['author'].values[0]
                synopsisstring = df_row['submit synopsis'].values[0]
                keywordstring = df_row['keywords'].values[0]
                pagewidthsstring = df_row['pagewidths'].values[0]
                pageheightsstring = df_row['pageheights'].values[0]
                pagecountstring = df_row['pagecount'].values[0]
                tokensintext = df_row['tokens in text'].values[0]
                # source = base path for file name
                source = filename.split('/')[-3] + '/' + filename.split('/')[-2]
                # basesource = top two levels of path

                resizingstring = df_row['pageresizingneeded'].values[0]
                specs_add_row_df = pd.DataFrame.from_dict(
                    {'title': titlestring, 'subtitle': subtitlestring, 'author': authorstring,
                     'Publisher-supplied synopsis': synopsisstring,
                     'Publisher-supplied Keywords': keywordstring, 'ISBN': 'ISBN TK',
                     'contributing editor': 'Cincinnatus',
                     'filename': str(filename), 'success': True, 'source': source, 'select': False, 'flags': '',
                     'PDF needs resizing': resizingstring, 'pagewidths': pagewidthsstring,
                     'pageheights': pageheightsstring, 'pagecount': pagecountstring, 'tokens in text': tokensintext},
                    orient='index').T

                print("specs_add_row_df: ", specs_add_row_df)
                # specs_add_row_df.fillna('', inplace=True).astype(str)
            except Exception as e:
                print("error creating specs_add_row_df")
                print(str(e))
                traceback.print_exc()

            try:
                df_row.to_csv(output_dir + "/dfrow.csv", index=False)
                success += 1
            except Exception as e:
                print("error writing to cumulative_df: " + filename)
                print(e)
                errors += 1

            filecount += 1
            st.write(f"filecount is {filecount}", f"batch_limit is {batch_limit}")
            st.write(f"filename is {filename}")
            print(f"filecount is {filecount} out of {number_of_files} total and batch_limit is {batch_limit}")
            if filecount == batch_limit:
                print("reached limit of files to process")
                break
            # st.write(cumulative_df, df_row)
            try:
                cumulative_df = pd.concat([cumulative_df, df_row])
            except Exception as e:
                print("error concatenating cumulative_df")
                print(e)
                traceback.print_exc()
            try:
                specs_input_df = pd.concat([specs_input_df, specs_add_row_df], ignore_index=True)
            except Exception as e:
                print("error concatenating specs_input_df")
                print(e)
                traceback.print_exc()
        if filecount >= 2:
            # st.write(cumulative_df.columns)
            cumulative_df = cumulative_df.sort_values(
                by=['pageresizingneeded'], ascending=True
            )
            candidates_prioritized_by_ease = cumulative_df[
                cumulative_df['pageresizingneeded'] == False
                ].sort_values(by=['pagecount'], ascending=False)
            # if candidates prioritized by ease is not None and is not empty:
            if not candidates_prioritized_by_ease.empty:
                print("candidates_prioritized_by_ease: ")
                print(candidates_prioritized_by_ease)
                candidates_prioritized_by_ease.to_csv(
                    output_dir + "/" + "candidates_prioritized_by_ease.csv")
        else:
            print("less than two files, no need to prioritize easy candidates")

        cumulative_file_name = timestamped_filename
        if not os.path.exists(output_dir + "/" + "job_results"):
            os.mkdir(output_dir + "/" + "job_results")

        cumulative_df.to_csv(
            output_dir + "/" + "job_results" + "/" + cumulative_file_name, index=False
        )

        cumulative_df.to_csv(output_dir + "/" + "cumulative_metadata.csv", index=False)
        print("success: " + str(success), "errors: " + str(errors))
        print("custom config files found: " + str(config_file_count))
        cumulative_df.to_excel(
            output_dir + "/" + "job_results" + "/" + timestamped_filename + ".xlsx",
            index=False,
        )
        cumulative_df.to_json(
            output_dir + "/job_results/" + timestamped_filename + ".json", orient="records"
        )
        distribution_reqts = book_metadata_json2distributor_format_targets()[2]
        # create 4-digit convenience uuid
        shortuuid = str(uuid.uuid4())[:4]
        try:
            specs_input_df.to_csv('output/job_results/' + shortuuid + '_metadata_stub_for_production_specs.csv',
                                  index=True, header=True)
        except Exception as e:
            print("error writing specs_input_df")
            print(e)

    def check_for_config_file(config, config_file_count, shortname):
        # check for custom configuration file
        shortname_config = shortname.with_suffix(".config")
        if os.path.exists(shortname_config):
            config_file = str(shortname_config)
            config_file_count += 1
            print("found config file: ", config_file)
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    print(config)
                    # exit()

            except Exception as e:
                print("error loading config file: " + config_file)
                print(e)
        return config, config_file_count

    def argparse_handler(args=None):
        argparser = argparse.ArgumentParser()

        argparser.add_argument("--limit", help="limit", default=1200)
        argparser.add_argument(
            "--list2string",
            help="output converted text as single string, not a list",
            default=False,
        )

        argparser.add_argument(
            "--pdf_directory",
            help="The directory of the files to be processed",
            default="working/public_domain",
        )
        argparser.add_argument(
            "--output_dir", help="path to output directory", default="output"
        )

        argparser.add_argument("--working_dir", help="working_dir", default="working")
        argparser.add_argument(
            "--cumulative_file_name",
            help="cumulative_file_name",
            default="output/cumulative_metadata.csv",
        )
        argparser.add_argument(
            "--profiling",
            help="create pandas profile report, time consuming",
            default=False,
        )
        argparser.add_argument("--checkamazon", default=False, action="store_true")
        argparser.add_argument("--payservices", default=False, action="store_true")
        argparser.add_argument(
            "--model", default="gpt-3.5-turbo", help="override preset engine"
        )
        argparser.add_argument("--run-recursive-summarizer", default=False, action="store_true",
                               help="run expensive recursive summarizer")
        argparser.add_argument("--single-file-path", default=None, help="run against just one file")
        argparser.add_argument("--run-page-by-page", default=False, action="store_true",
                               help="run page by page analysis of pdf")
        argparser.add_argument("--ai-metadata", default=False, action="store_true",
                               help="use AI to generate narrative metadata")
        argparser.add_argument("--create-postscript-file", default=False, action="store_true",
                               help="create postscript file for convenience; slow, but faster than Acrobat")
        argparser.add_argument("--mode", default="assess", help="assess, produce")
        argparser.add_argument("--batch-limit", default="5", help="limit number of files to process")
        argparser.add_argument("--production-specs-filepath", default="test/csv/testing_specs.csv", help=
        "path to specific production specs file")
        argparser.add_argument("--add-to-final", default=False, help="add this table to final_LSI_ACS.csv",
                               action="store_true")
        argparser.add_argument("--skip-spec-check", default=False, help="skip checking for production spec",
                               action="store_true")
        args = argparser.parse_args()
        pdf_directory = args.pdf_directory
        limit = args.limit
        skip_spec_check = args.skip_spec_check
        output_dir = args.output_dir
        list2string = args.list2string
        cumulative_file_name = args.cumulative_file_name
        working_dir = args.working_dir
        profiling = args.profiling
        payservices = args.payservices
        run_recursive = args.run_recursive_summarizer
        single_file_path = args.single_file_path
        run_page_by_page = args.run_page_by_page
        ai_metadata = args.generate_ai_narratives
        create_interior_postscript = args.create_postscript_file
        mode = args.mode
        batch_limit = args.batch_limit
        production_specs_filepath = args.production_specs_filepath
        add_to_final = args.add_to_final
        model = args.model

        return (
            pdf_directory,
            output_dir,
            list2string,
            cumulative_file_name,
            limit,
            working_dir,
            profiling,
            payservices,
            model,
            run_recursive,
            single_file_path,
            run_page_by_page,
            ai_metadata,
            create_interior_postscript,
            mode,
            batch_limit,
            production_specs_filepath, add_to_final
        )
