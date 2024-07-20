
#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

# logger = logging.getLogger('nimble')
# gpt3 completion object
import argparse
import json
import logging
import os
import re
import traceback
import uuid

import streamlit as st
import stripe
# from transformers import GPT2TokenizerFast
import tiktoken
from groq import Groq
from openai import OpenAI

encoding = tiktoken.get_encoding("p50k_base")
encoding35 = tiktoken.get_encoding("p50k_base")
encoding35 = tiktoken.get_encoding("cl100k_base")

stripe_keys = {
    "secret_key": os.environ["STRIPE_SECRET_KEY"],
    "publishable_key": os.environ["STRIPE_PUBLISHABLE_KEY"],
    "price_id": os.environ["STRIPE_PRICE_ID"],
    "endpoint_secret": os.environ["STRIPE_ENDPOINT_SECRET"],
}

stripe.api_key = stripe_keys["secret_key"]


import openai


openai_user_id_for_safety_tracking = os.environ['OPENAI_USER_ID_FOR_SAFETY_TRACKING']

import pandas as pd
import backoff

from classes.Utilities.geminicomplete import generate_response




client = OpenAI()

def count_tokens(text):
    tokens_counted = len(encoding.encode(text))
    return tokens_counted


def presets_parser(preset_filename):
    # logging.debug(preset_filename)
    try:
        openfile = "app/presets/" + preset_filename + ".json"

        presetsdf = pd.read_json(openfile, dtype=object)
        logging.info('opening file %s', openfile)
    except Exception as e:
        logging.info('could not open file', openfile)
        presetsdf = pd.DataFrame()
    presetsdf['preset_name'] = presetsdf.get('preset_name', "Presets")
    presetsdf['preset_pagetype'] = presetsdf.get('preset_pagetype', "UserPrompt")
    presetsdf['preset_description'] = presetsdf.get('preset_description', "Description of this preset.")
    presetsdf['preset_instructions'] = presetsdf.get('preset_instructions', "Fill in the form.")
    presetsdf['preset_placeholder'] = presetsdf.get('preset_placeholder', "Enter this text:")
    presetsdf['pre_user_input'] = presetsdf.get('pre_user_input', "")
    presetsdf['prompt'] = presetsdf.get('prompt', "")
    presetsdf['post_user_input'] = presetsdf.get('post_user_input', "")
    presetsdf['preset_additional_notes'] = presetsdf.get('preset_additional_notes', "Notes:")

    # request parameters

    presetsdf['engine'] = presetsdf.get('engine', "ada")
    presetsdf['suffix'] = presetsdf.get('suffix', "")
    presetsdf['finetune_model'] = presetsdf.get('finetune_model', "")
    presetsdf['temperature'] = presetsdf.get('temperature', 0.7)
    presetsdf['max_tokens'] = presetsdf.get('max_tokens', 100)
    presetsdf['top_p'] = presetsdf.get('top_p', 1.0)
    presetsdf['fp'] = presetsdf.get('fp', 0.5)
    presetsdf['pp'] = presetsdf.get('pp', 0.5)
    presetsdf['stop_sequence'] = presetsdf.get('stop_sequence', ["\n", "<|endoftext|>"])
    presetsdf['echo_on'] = presetsdf.get('echo_on', False)
    presetsdf['search_model'] = presetsdf.get('search_model', "ada")
    presetsdf['model'] = presetsdf.get('model', "curie")
    presetsdf['question'] = presetsdf.get('question', "")
    presetsdf['fileID'] = presetsdf.get('answerhandle', "")
    presetsdf['examples_context'] = presetsdf.get('examples_context', "In 2017, U.S. life expectancy was 78.6 years.")
    presetsdf['examples'] = presetsdf.get('examples',
                                          '[["What is human life expectancy in the United States?", "78 years."]]')
    presetsdf['max_rerank'] = presetsdf.get('max_rerank', 10)

    # specify secure db for Journals
    presetsdf['preset_db'] = presetsdf.get('preset_db', 'None')

    # metadata

    presetsdf['user'] = presetsdf.get('user', 'testing')
    presetsdf['organization'] = presetsdf.get('organization', 'org-M5QFZNLlE3ZfLaRw2vPc79n2')  # NimbleAI

    # logging.debug df for convenience
    transposed_df = presetsdf.set_index('preset_name').transpose()
    # logging.debug('transposeddf', transposed_df)

    # now read into regular variables

    preset_name = presetsdf['preset_name'][0]
    preset_pagetype = presetsdf['preset_pagetype'][0]
    preset_description = presetsdf['preset_description'][0]
    preset_instructions = presetsdf['preset_instructions'][0]
    preset_placeholder = presetsdf['preset_placeholder'][0]
    preset_additional_notes = presetsdf['preset_additional_notes'][0]
    pre_user_input = presetsdf['pre_user_input'][0]
    post_user_input = presetsdf['post_user_input'][0]
    prompt = presetsdf['prompt'][0]
    engine = presetsdf['engine'][0]
    suffix = presetsdf['suffix'][0]
    finetune_model = presetsdf['finetune_model'][0]
    temperature = presetsdf['temperature'][0]
    max_tokens = presetsdf['max_tokens'][0]
    top_p = presetsdf['top_p'][0]
    fp = presetsdf['fp'][0]
    pp = presetsdf['pp'][0]
    stop_sequence = presetsdf['stop_sequence'][0]
    if presetsdf['echo_on'][0] == 'True':
        echo_on = True
    else:
        echo_on = False

    search_model = presetsdf['search_model'][0]
    model = presetsdf['model'][0]
    question = presetsdf['question'][0]
    fileID = presetsdf['fileID'][0]
    examples_context = presetsdf['examples_context'][0]
    examples = presetsdf['examples'][0]
    max_rerank = presetsdf['max_rerank'][0]
    preset_db = presetsdf['preset_db'][0]
    user = presetsdf['user'][0]
    organization = presetsdf['organization'][0]

    # then return both df and regular variables

    return presetsdf, preset_name, preset_description, preset_instructions, preset_additional_notes, preset_placeholder, pre_user_input, post_user_input, prompt, engine, suffix, finetune_model, temperature, max_tokens, top_p, fp, pp, stop_sequence, echo_on, preset_pagetype, preset_db, user, organization


def construct_preset_dict_for_UI_object(list_of_presets):
    preset_dir = "app/presets/"
    dict_of_presets_for_UI_object = {}
    for preset in list_of_presets:
        this_preset_file = preset_dir + preset + ".json"
        list_for_object = []
        with open(this_preset_file, 'rb') as f:
            this_preset = json.load(f)
            row = [preset, this_preset['preset_name']]
            list_for_object.append(row)
        dict_of_presets_for_UI_object = dict(list_for_object)

    return dict_of_presets_for_UI_object


@backoff.on_exception(backoff.expo, openai.OpenAIError, max_tries=5, logger='root')
def chatcomplete(preset_filename: object, prompt: object, engine: object, username: object = "guest",
                 temperature: object = 1, fpsuffix: object = None,
                 echo_on: object = False,
                 max_tokens: object = 3000, helicone: object = True, verbose: object = False,
                 model: object = None) -> object:
    logging.debug('-----Entering chatcomplete-----')

    logging.info(f"helicone switch is {helicone}")
    # version without function calls
    override_prompt = None
    if model:
        engine = model
    logging.info('model (engine) is %s', engine)

    openai_user_id_for_safety_tracking = os.environ['OPENAI_USER_ID_FOR_SAFETY_TRACKING']

    if prompt:
        override_prompt = prompt
    if engine:
        override_engine = engine  # will override preset engine spec

    if preset_filename is not None:
        try:
            presetsdf, preset_name, preset_description, preset_instructions, preset_additional_notes, preset_placeholder, pre_user_input, post_user_input, prompt, engine, suffix, finetune_model, temperature, max_tokens, top_p, fp, pp, stop_sequence, echo_on, preset_pagetype, preset_db, user, organization = presets_parser(
                preset_filename)
            # logging.debug(presetsdf.T)
        except Exception as e:
            # create json error response in format ['choices'][0]['message']['content'] = "error in presets_parser" + str(e)
            logging.error("error in presets_parser", e)
            logging.error(e)
            return

        if override_prompt:
            prompt = override_prompt
        if override_engine:
            engine = override_engine

        inputmsg = pre_user_input + '\n\n' + post_user_input

        logging.debug(inputmsg)
        promptsubmit = pre_user_input + prompt + '\n\n' + post_user_input
        infomessage = f"Submitting request via {preset_name} to {engine} with parameters {promptsubmit}, {temperature}, {max_tokens}, {top_p}, {fp}, {pp}, {stop_sequence}, {echo_on}, {user}, {helicone}, {openai.base_url}"
        # logging.debug(infomessage)
        logging.debug(infomessage)
        if verbose:
            logging.debug(infomessage)

        if openai_user_id_for_safety_tracking is None:
            openai_user_id_for_safety_tracking = str(6)

        for item in promptsubmit:
            promptchar = len(item)

        if helicone:
            openai.base_url = "https://oai.hconeai.com/v1"
            helicone_header = get_helicone_header(preset_filename)
        #logging.debug(os.environ['HELICONE_API_KEY'], logging.debug(type(os.environ['HELICONE_API_KEY'])))

        if engine == "groq":
            try:
                groqclient = Groq(api_key=os.getenv("GROQ_API_KEY"))
                response = groqclient.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[
                        {"role": "user", "content": promptsubmit}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p, )
                # logging.debug(response)
                #logging.debug(response.choices[0].message.content)
                response_text = response.choices[0].message.content
            except Exception as e:
                traceback.print_exc()
                st.write(traceback.print_exc())
            return response_text

        elif "gemini" in engine:
            print(engine)
            prompt_parts = prompt
            logging.debug(prompt_parts)
            logging.debug(engine)
            response = generate_response(engine, prompt_parts, stream_response=False)
            response_text = response
            return response_text

        else:
            try:

                response = client.chat.completions.create(
                    model=engine,
                    messages=[
                        {"role": "user", "content": promptsubmit}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p)
                logging.info("valid response received")
                logging.debug(response)
                response_text = response.choices[0].message.content
            except Exception as e:
                logging.error(f"error in chatcomplete {e}")
                st.write(f"error in chatcomplete {e}")
            #response_text = presetsdf['completion_heading'][0] + '\n'


        return response_text


def get_helicone_header(preset_filename):
    key = os.environ['HELICONE_API_KEY']
    helicone_header = {"Helicone-Auth": f"Bearer {key}"}

    return helicone_header
def gpt3complete(preset_filename, prompt, engine, username="guest", temperature=1, fpsuffix=None, echo_on=False,
                 helicone=True):
    override_prompt = None

    logging.debug('engine is %s', engine)

    openai_user_id_for_safety_tracking = os.environ['OPENAI_USER_ID_FOR_SAFETY_TRACKING']
    if helicone:
        openai.base_url = "https://oai.hconeai.com/v1"
        key = os.environ['HELICONE_API_KEY']
        # logging.debug(key)
    # logging.debug(type(key))
    if prompt:
        override_prompt = prompt
    if engine:
        override_engine = engine

    presetsdf, preset_name, preset_description, preset_instructions, preset_additional_notes, preset_placeholder, pre_user_input, post_user_input, prompt, engine, suffix, finetune_model, temperature, max_tokens, top_p, fp, pp, stop_sequence, echo_on, preset_pagetype, preset_db, user, organization = presets_parser(
        preset_filename)
    #logging.debug(presetsdf.T)
    if override_prompt:
        prompt = override_prompt

    if override_engine:
        engine = override_engine
    logging.debug(pre_user_input, prompt, post_user_input)
    promptsubmit = pre_user_input + prompt + '\n' + post_user_input

    logging.info('promptsubmit is:', promptsubmit)

    if openai_user_id_for_safety_tracking is None:
        openai_user_id_for_safety_tracking = str(6)

    for item in promptsubmit:
        promptchar = len(item)

    if engine.startswith("gpt-3"):
        st.info("using chatcomplete instead of gptcomplete")
        response = chatcomplete(preset_filename, prompt, engine, username="guest", temperature=1, fpsuffix=None,
                                echo_on=False,
                                helicone=True)
    else:
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                prompt=promptsubmit,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=fp,
                presence_penalty=pp,
                user=openai_user_id_for_safety_tracking,
                headers={
                    "Helicone-Property-Preset": preset_filename,
                    "Helicone-Cache-Enabled": "false",
                    "Helicone-Auth": f"Bearer {key}"}
            )
            logging.ebug(response)
        except ValueError:
            st.write(ValueError)
            st.error("Error: ValueError")

    response_text = "#### " + presetsdf['completion_heading'][0] + '\n'
    response_text = response_text + response.choices[0].message.content

    return response_text
    # remember that this change breaks the return function to all apps calling this library -- they must select the list item they want






def create_uuid():
    return str(uuid.uuid4())


def post_process_text(text, options="all"):
    # all_patterns = [r'<br\s*?>', r'<br>', r'<li>', r'\n\s*\n', r'^-\s+', r'^-', r'\d+[)]'
    # combined_patterns =  = r'|'.join(map(r'(?:{})'.format, all_pats))
    text = text.replace('<br\\s*?>', '')
    text = text.replace('<br>', '\n')
    text = text.replace('<li>', '\n')
    text = re.sub(r'\d+[)]', "", text)
    text = text.replace('\n-', '\n')
    text = text.replace('\n• ', '\n')
    text = text.replace('\n ', '\n')
    text = re.sub('[\n]+', '\n', text)
    text = re.sub('\\d+[.]\\s+', '', text).rstrip()
    text = re.sub('\\d+[.\n]\\s+', '', text).rstrip()
    #text = re.sub('^.{0,15}$', '', text)  # remove short lines
    text = text.replace('\\n', '\n')
    text = re.sub('[\n]+', '\n', text)
    text = text.replace('###', '\n\n')
    # logging.debug('post processed text is', '\n' + text)
    return text


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()

    argparser.add_argument('--preset', type=str, default="ELI5")
    argparser.add_argument('--prompt', type=str, default="What is a test?")
    argparser.add_argument('--engine', type=str, default="gpt-4o")
    argparser.add_argument('--suffix', type=str, default=None)
    args = argparser.parse_args()
    prompt = args.prompt
    preset = args.preset
    engine = args.engine
    suffix = args.suffix
    logging.debug(openai.__version__)
    logging.debug(openai.base_url)
    logging.debug(openai.api_key)
    logging.debug('args= ',
                 preset, prompt, engine, suffix)
    result = chatcomplete(preset, prompt, "gpt-3.5-turbo", helicone=True)
    logging.debug(result)
    logging.debug(result)
