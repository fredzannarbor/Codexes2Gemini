#  Copyright (c) 2024. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com
import logging

from classes.SyntheticAuthors.DanielDefoe.DanielDefoe import CodexSpecs2Book


class DefoeHelpers(CodexSpecs2Book):
    def extract_paragraphs_from_results(self, results_df):
        rows_list = []
        title = results_df.loc[results_df['Unnamed: 0'] == 'title', '1'].iloc[0]
        rows_list.append({"para_text": title, "table_id": "NoValue", "style": "Heading 1"})

        chapters_str = results_df.loc[results_df['Unnamed: 0'] == 'chapters', '1'].iloc[0]
        chapters_list = ast.literal_eval(chapters_str)

        for chapter in chapters_list:
            chapter_title = chapter.get('Title', '')
            rows_list.append({"para_text": chapter_title, "table_id": "NoValue", "style": "Heading 2"})

            scenes = chapter.get('List of Scenes', [])
            for scene in scenes:
                scene_text = scene.get('scene text', "")
                if isinstance(scene_text, str):
                    paragraphs = [para.strip() for para in scene_text.split('\n') if para.strip()]
                    for paragraph in paragraphs:
                        rows_list.append({"para_text": paragraph, "table_id": "NoValue", "style": "Body Text"})

        new_df = pd.DataFrame(rows_list)
        output_path = "output/extracted_paragraphs.csv"
        new_df.to_csv(output_path, index=False)

        logging.info(f"Data has been saved to: {output_path}")
        return new_df

    def ensure_unique_short_titles(self, df):
        """
        Ensures that the values in the 'short_title' column of the DataFrame are unique.
        If duplicates are found, appends a count to make each 'short_title' unique.

        Parameters:
            df (pandas.DataFrame): The DataFrame to process.

        Returns:
            pandas.DataFrame: The DataFrame with ensured unique 'short_title' values.
        """
        # Identify duplicates
        duplicates = df.duplicated(subset='short_title', keep=False)  # `keep=False` marks all duplicates as True

        # Only work on duplicates
        if duplicates.any():
            print("Warning: There are duplicated short titles in your dataframe.")

            # Adjusting to ensure the first instance of a title doesn't get altered if it's not a duplicate.
            # Generating a suffix only for duplicates (starting from the second occurrence)
            def make_unique(title, idx):
                if idx != 0:  # Start appending numbers from the second occurrence onwards
                    return f"{title}_{idx + 1}"
                return title

            # Applying the adjustment to only duplicates
            for title, group in df[duplicates].groupby('short_title'):
                # Apply make_unique function to each group of duplicates, excluding the first occurrence
                unique_titles = [make_unique(title, idx) for idx in range(len(group))]
                df.loc[group.index, 'short_title'] = unique_titles

        return df
