'''
Utilities to calibrate the synthetic reader
- rate the same ideas repeatedly, and see if the same idea gets the same score
'''
import json

import pandas as pd
import plotly.express as px
import spacy
import streamlit as st
# from llama_index.indices.query.response_synthesis import ResponseSynthesizer
# from llama_index import (SimpleDirectoryReader, StorageContext,
#                          ListIndex)
# from llama_index.langchain_helpers.text_splitter import TokenTextSplitter
# from llama_index.llms import OpenAI
# from llama_index.node_parser import SimpleNodeParser
# from llama_index.storage.docstore import SimpleDocumentStore
# from llama_index.storage.index_store import SimpleIndexStore
# from llama_index.vector_stores import SimpleVectorStore
from nltk.sentiment import SentimentIntensityAnalyzer
from textblob import TextBlob

nlp = spacy.load('en_core_web_sm')

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

# from classes.SyntheticReaders import Reader
from app.utilities.gpt3complete import chatcomplete
# from app.utilities.files2llamaindex
# from app.utilities.preset2servicecontext import preset_reader

import re

def remove_initial_non_numeric(s):
    return re.sub(r'^\D*', '', s)
def rate_paras(paras_df, panel, preset, num_rows):
    para_count = 0
    paras_df['word_count'] = paras_df['para'].apply(lambda x: len(x.split()))
    paras_df['sentence_count'] = paras_df['para'].apply(lambda x: len(list(nlp(x).sents)))
    results_df = pd.DataFrame()
    for index, para_row in paras_df.iterrows():
        # enhance paras_df with word count and sentence count

            # skip certain rows
        if para_count < 0:
            para_count += 1
            continue
        # get the para
        para = paras_df['para'].iloc[para_count]
        st.info(f"para: {para}")

        if para_count % 500 == 0:
            print(f"para_count: {para_count} of {paras_df.shape[0]}")
        # skip rows that are hard to evaluate
        if para_row['para'] == '' or para_row['para'] == '\n':
            continue
        if para_row['word_count'] == 0:
            continue
        if para_row['sentence_count'] == 0:
            continue

        for index, reader in panel.iterrows():
            # loop through the attributes of each reader
            # assemble them all into a block of text
            block = "Attributes:\n"

            for attribute, value in reader.items():
                add2prefix = f"{attribute}: {value}"
                block = block + f"\n{add2prefix}\n"
                para_with_prefix = f"{block}\n Idea: {para}\n\n"

            number_of_readers = panel.shape[0]
            if (para_count + 1) / 20 == 0:
                spinnermessage = f"{reader['name']}, {index + 1} of  {number_of_readers} Readers, is evaluating  {str(para_count + 1)} of {str(paras_df.shape[0])} paragraphs."
            else:
                spinnermessage = None
            with st.spinner(spinnermessage):
                try:
                    response_text = chatcomplete(preset, para_with_prefix, "gpt-3.5-turbo")

                    result = response_text
                except Exception as e:
                    errormessage = f"Error on openai request. {e}"
                    result = "API Error"
                    st.error(errormessage)
                    continue

                # if result begins with a non-numeric character, remove all non-numeric characters from the beginning of the string
                result = remove_initial_non_numeric(result)
                row_data = {'Reader': reader['name'], 'Para': para, 'Evaluation': result}


                row_data = {'Reader': reader['name'], 'Para': para, 'Evaluation': result}
                #st.info(f"row_data: {row_data}")
                row_df = pd.DataFrame(row_data, index=[0], columns=['Reader', 'Para', 'Evaluation'])
                scoremsg = f"Net score by {reader['name']}: {result}"
                st.success(scoremsg)
                #st.write(row_df)
                results_df = pd.concat([results_df, row_df])
        para_count += 1
        if para_count > num_rows - 1:
            break
    results_df = results_df.reset_index(drop=True)
    results_df.to_excel("working/para_rating_results.xlsx")
    return results_df



def rate_ideas(ideas_df, panel, preset, num_rows):
    idea_count = 0
    #st.info(ideas_df    )
    ideas_df['word_count'] = ideas_df['Idea'].apply(lambda x: len(x.split()))
    ideas_df['sentence_count'] = ideas_df['Idea'].apply(lambda x: len(list(nlp(x).sents)))
    results_df = pd.DataFrame()
    for index, idea_row in ideas_df.iterrows():
        # enhance ideas_df with word count and sentence count

            # skip certain rows
        if idea_count < 0:
            idea_count += 1
            continue
        # get the idea
        idea = ideas_df['Idea'].iloc[idea_count]
        st.info(f"idea: {idea}")

        if idea_count % 500 == 0:
            print(f"idea_count: {idea_count} of {ideas_df.shape[0]}")
        # skip rows that are hard to evaluate
        if idea_row['Idea'] == '' or idea_row['Idea'] == '\n':
            continue
        if idea_row['word_count'] == 0:
            continue
        if idea_row['sentence_count'] == 0:
            continue

        for index, reader in panel.iterrows():
            # loop through the attributes of each reader
            # assemble them all into a block of text
            block = "Attributes:\n"

            for attribute, value in reader.items():
                add2prefix = f"{attribute}: {value}"
                block = block + f"\n{add2prefix}\n"
                idea_with_prefix = f"{block}\n Idea: {idea}\n\n"

            number_of_readers = panel.shape[0]
            spinnermessage = f"{reader['name']}, {index + 1} of  {number_of_readers} Readers, is evaluating  {str(idea_count + 1)} of {str(ideas_df.shape[0])} ideas."
            with st.spinner(spinnermessage):
                try:
                    response_text = chatcomplete(preset, idea_with_prefix, "gpt-3.5-turbo")
                    result = response_text
                except Exception as e:
                    errormessage = f"Error on openai request. {e}"
                    result = "API Error"
                    st.error(errormessage)
                    continue

                sentiments = sentiment_test(result)
                openai_sentiment_result = open_ai_sentiment_analysis(result)

                openai_sentiment_number = openai_sentiment_result[0]
                openai_explanation = openai_sentiment_result[1]

                row_data = {'Reader': reader['name'], 'Idea': idea, 'Evaluation': result, 'OpenAI Sentiment' : openai_sentiment_number, 'OpenAI Explanation': openai_explanation, 'textblob_polarity': sentiments[1], 'textblob_subjectivity': sentiments[2], 'vader_compound': sentiments[0], 'flairval': sentiments[3]}


                row_df = pd.DataFrame(row_data,  columns=['Reader', 'Idea', 'Evaluation','OpenAI Sentiment', 'OpenAI Explanation',  'textblob_polarity', 'textblob_subjectivity', 'vader_compound', 'flairval'], index=[0])
                openai_sentiment_number = round(openai_sentiment_number, 2)
                print(type(openai_sentiment_number))
                col1, col2 = st.columns([2,1])
                scoremsg = f"Evaluation by {reader['name']}: {result}"
                col1.success(scoremsg)
                col2.metric(label="OpenAI Sentiment", value=openai_sentiment_number)
                col2.info(f"Explanation: {openai_explanation}")

                #st.write(row_df)
                results_df = pd.concat([results_df, row_df])
        idea_count += 1
        if idea_count > num_rows - 1:
            break
    results_df = results_df.reset_index(drop=True)
    results_df.to_excel("working/idea_rating_results.xlsx")
    #spreadsheet(results_df, key='idea_rating_results')
    return results_df


def rate_objects(objects_df, panel_df, presets, num_rows, model, object_key, openai_sentiment_evaluation=False):
    count = 0
   #st.write(objects_df, panel, presets, num_rows)
    objects_df['word_count'] = objects_df[object_key].apply(lambda x: len(x.split()))
    objects_df['sentence_count'] = objects_df[object_key].apply(lambda x: len(list(nlp(x).sents)))
    results_df = pd.DataFrame()
    for index, object_row in objects_df.iterrows():
        # enhance ideas_df with word count and sentence count

        # skip certain rows
        if count < 0:
            count += 1
            continue
        # get the object
        object_value = objects_df[object_key].iloc[count]
        #st.info(f"object_value: {object_value}")

        if count % 500 == 0:
            print(f"count: {count} of {objects_df.shape[0]} of {object_key}")
        # skip rows that are hard to evaluate
        if object_key == '' or object_key == '\n':
            continue

        for index, reader in panel_df.iterrows():
            # loop through the attributes of each reader
            # assemble them all into a block of text
            block = "Attributes:\n"

            for attribute, value in reader.items():
                add2prefix = f"{attribute}: {value}"
                block = block + f"\n{add2prefix}\n"
                idea_with_prefix = f"{block}\n Object key: {object_key}\n\n"

            number_of_readers = panel_df.shape[0]
            spinnermessage = f"{reader['name']}, {index + 1} of  {number_of_readers} Readers, is evaluating  {str(count + 1)} of  {num_rows} selected from a total of {str(objects_df.shape[0])} {object_key}(s)."
            with st.spinner(spinnermessage):
                for p in presets:
                    try:
                        response_text = chatcomplete(p, idea_with_prefix, model)
                        result = response_text
                    except Exception as e:
                        errormessage = f"Error on openai request. {e}"
                        traceback.print_exc()
                        result = "API Error"
                        st.error(errormessage)
                        continue
                    # load result as json
                    try:
                        jresult = json.loads(result)
                    except Exception as e:
                        errormessage = f"Error loading json. {e}"
                        st.error(errormessage)
                        result = "Json loading error"
                        continue
                    # loop through json key/value pairs
                    for key, value in jresult.items():
                        # if the key is the same as the object key, then get the value
                        if key == object_key:
                            result = value
                            break
                        else:
                            continue

                sentiments = sentiment_test(result)
                if openai_sentiment_evaluation:
                    openai_sentiment_result = open_ai_sentiment_analysis(result)
                    openai_sentiment_number = openai_sentiment_result[0]
                    openai_explanation = openai_sentiment_result[1]
                else:
                    openai_sentiment_number = "N/A"
                    openai_explanation = "N/A"

                row_data = {'Reader': reader['name'], 'Object Value': object_value, 'Evaluation': result,
                            'OpenAI Sentiment': openai_sentiment_number, 'OpenAI Explanation': openai_explanation,
                            'textblob_polarity': sentiments[1], 'textblob_subjectivity': sentiments[2],
                            'vader_compound': sentiments[0], 'flairval': sentiments[3]}

                row_df = pd.DataFrame(row_data, columns=['Reader', 'Object Value', 'Evaluation', 'OpenAI Sentiment',
                                                         'OpenAI Explanation', 'textblob_polarity',
                                                         'textblob_subjectivity', 'vader_compound', 'flairval'],
                                      index=[0])
                #display_evaluations(object_value, openai_explanation, openai_sentiment_evaluation,openai_sentiment_number, reader, result)

                # st.write(row_df)
                results_df = pd.concat([results_df, row_df])
        count += 1
        if count > num_rows - 1:
            break
    results_df = results_df.reset_index(drop=True)
    results_df.to_excel("working/object_rating_results.xlsx")
    return results_df


def display_evaluations(object_value, openai_explanation, openai_sentiment_evaluation, openai_sentiment_number, reader,
                        result):
    col1, col2 = st.columns([2, 1])
    scoremsg = f"Evaluation by {reader['name']}: {result}"
    col1.success(scoremsg)
    if openai_sentiment_evaluation:
        if isinstance(object_value, float):
            openai_sentiment_number = round(openai_sentiment_number, 2)
            col2.metric(label="OpenAI Sentiment", value=openai_sentiment_number)
        col2.info(f"Explanation: {openai_explanation}")


def open_ai_sentiment_analysis(result):
    openai_sentiment_response = chatcomplete("SentimentAnalysis", result, "gpt-3.5-turbo")
    print(f"openai_sentiment_response: {openai_sentiment_response}")
    # Parse the content
    data = json.loads(openai_sentiment_response)

    # Extract the message content and parse it as JSON


    # Extract the explanation and score
    explanation = data['explanation']
    score = data['score']

    print('Explanation:', explanation)
    print('Score:', score)
    return score, explanation


def sentiment_test(result):
    sia = SentimentIntensityAnalyzer()
    vader_compound = sia.polarity_scores(result)['compound']

    textblob_polarity = TextBlob(result).sentiment.polarity
    textblob_subjectivity = TextBlob(result).sentiment.subjectivity

    # classifier = TextClassifier.load('en-sentiment')
    # sentence = Sentence(result)
    # classifier.predict(sentence)
    flairval = "N/A" #sentence.labels[0].score

    return vader_compound, textblob_polarity, textblob_subjectivity, flairval

def visualize_object_df(object_df):


    # Load your data (you'll need to adjust the path or method of loading)
    data = object_df
    data['Evaluation'] = data['enjoy']

    # convert data json to boolean and string values
    data['Evaluation'] = data['Evaluation'].apply(lambda x: True if x == 'True' else False)


    grouped_data = data.groupby('Object Value')['Evaluation'].mean().reset_index()
    grouped_data['short_label'] = grouped_data['Object Value'].str[:15]

    # Create the Plotly figure
    fig = px.bar(grouped_data, x='short_label', y='Evaluation',
                 labels={'short_label': 'Paragraph Snippet', 'Evaluation': 'Proportion of Positive Evaluations'},
                 title='Reader Evaluation of Paragraphs')
    fig.update_layout(
        xaxis_tickangle=0,
        xaxis_title="Paragraph Snippet",
        yaxis_title="Proportion of Positive Evaluations",
        bargap=0.1,
        bargroupgap=0.1
    )

    # Embed the plot in Streamlit
    st.plotly_chart(fig)
    return


def evaluate_rating_consistency(all_results_df):
# loop through the ideas
    # loop through the readers
    # loop through the readers again
    # if the reader is the same, then compare the ratings
    # if the reader is different, then compare the ratings
    # if the ratings are the same, then add 1 to the count
    # if the ratings are different, then add 0 to the count
    # divide the count by the number of comparisons
    # return the result
    #st.write(all_results_df)
    count = 0
    total = 0
    for idea in all_results_df['Idea'].unique():
        #st.write(idea)
        idea_df = all_results_df[all_results_df['Idea'] == idea]
        #st.write(idea_df)
        for reader1 in idea_df['Reader'].unique():
            #st.write(reader1)
            reader1_df = idea_df[idea_df['Reader'] == reader1]
            #st.write(reader1_df)
            for reader2 in idea_df['Reader'].unique():
                #st.write(reader2)
                reader2_df = idea_df[idea_df['Reader'] == reader2]
                #st.write(reader2_df)
                if reader1 == reader2:
                    #st.write("same reader")
                    #st.write(reader1_df['Rating'].iloc[0])
                    #st.write(reader2_df['Rating'].iloc[0])
                    if reader1_df['Rating'].iloc[0] == reader2_df['Rating'].iloc[0]:
                        count += 1
                        total += 1
                    else:
                        total += 1
                else:
                    #st.write("different reader")
                    #st.write(reader1_df['Rating'].iloc[0])
                    #st.write(reader2_df['Rating'].iloc[0])
                    if reader1_df['Rating'].iloc[0] == reader2_df['Rating'].iloc[0]:
                        count += 0
                        total += 1
                    else:
                        total += 1
    return count / total

def evaluate_reader_consistency_per_idea(all_results_df):
    # when a reader has evaluated the same idea more than once, how consistent are they?
    # loop through the ideas
    # loop through the readers
    # if the reader has evaluated the idea more than once, then compare the ratings
    # if the ratings are the same, then add 1 to the count
    # if the ratings are different, then add 0 to the count
    # divide the count by the number of comparisons
    # return the result
    count = 0
    total = 0
    reader_consistency_df = pd.DataFrame()
    for idea in all_results_df['Idea'].unique():
        #st.write(idea)
        idea_df = all_results_df[all_results_df['Idea'] == idea]
        #st.write(idea_df)
        for reader in idea_df['Reader'].unique():
            #st.write(reader)
            reader_df = idea_df[idea_df['Reader'] == reader]
            #st.write(reader_df)
            if reader_df.shape[0] > 1:
                #st.write("reader has evaluated this idea more than once")
                #st.write(reader_df['Rating'].iloc[0])
                #st.write(reader_df['Rating'].iloc[1])
                if reader_df['Rating'].iloc[0] == reader_df['Rating'].iloc[1]:
                    count += 1
                    total += 1
                else:
                    total += 1
            run_consistency_df = pd.DataFrame({'Reader': reader, 'Idea': idea, 'Count': count, 'Total': total}, index=[0], columns=['Reader', 'Idea', 'Count', 'Total'])
        reader_consistency_df = pd.concat([reader_consistency_df, run_consistency_df])
        st.write(reader_consistency_df)
    return count, total


def rate_remits(completions_df, panel):
    results_df = pd.DataFrame()
    ideacount = 0
    # st.write(completions_df)
    for remit in completions_df['remit']:
        bio = completions_df['bio'].iloc[ideacount]

        # loop through the rows of the panel dataframe
        for index, reader in panel.iterrows():
            # loop through the attributes of each reader
            # assemble them all into a block of text
            block = "Attributes:\n"

            for attribute, value in reader.items():
                add2prefix = f"{attribute}: {value}"
                block = block + f"\n{add2prefix}\n"

            idea_with_prefix = f"{block}\n Remit: {remit}\nBio: {bio}\n"

            number_of_readers = panel.shape[0]
            spinnermessage = f"{reader['name']}, {index + 1} of  {number_of_readers} Readers, is evaluating  {str(ideacount + 1)} of {str(completions_df.shape[0])} ideas."
            with st.spinner(spinnermessage):
                try:
                    response_text = chatcomplete("EvaluateProposedRemits", idea_with_prefix, "gpt-3.5-turbo")
                    result = response_text
                # st.write('result', result)

                except Exception as e:
                    errormessage = f"Error on openai request. {e}"
                    st.error(errormessage)
                try:
                    remit_assessment = idea_with_prefix + '\n\n' + result
                    # rating = rating_response['choices'][0]['message']['content']
                except Exception as e:
                    errormessage = f"Error on openai request. {e}"
                    st.error(errormessage)

            # add the completion to the results dataframe
            row_df = pd.DataFrame(
                data={'Reader': reader['name'], 'Remit': remit, 'Result': result}, index=[0],
                columns=['Reader', 'Remit', 'Result'])
            results_df = pd.concat([results_df, row_df])
        ideacount += 1
        # drop index column
        results_df = results_df.reset_index(drop=True)
        results_df.to_excel("working/remit_rating_results.xlsx")
    return results_df


def llmjson2json(string):
    # convert llm pseudojson to validated json
    try:
        validjson = json.loads(string)
    except Exception as e:
        errormessage = f"Error converting llm pseudojson to json. {e}"
        st.error(errormessage)
        validjson = {'Classification': 'JsonError', 'Explanation': 'JsonError'}
    return validjson


    def extract_text_from_epub(file_path):
        book = epub.read_epub(file_path)
        paragraphs = []

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.content, 'html.parser')
            for p in soup.find_all('p'):
                paragraphs.append(p.get_text())

        return paragraphs
