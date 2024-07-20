import argparse
import logging
import os

import google.generativeai as genai


def configure_logging(log_level: str):
    numeric_level = getattr(logging, log_level.upper(), None)
    if numeric_level is None:
        raise ValueError(f'Invalid log level: {log_level}')
    logging.basicConfig(level=numeric_level, format='%(asctime)s - %(levelname)s - %(message)s')


def configure_api():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY environment variable is not set.")
    genai.configure(api_key=api_key)


def get_generation_config():
    return {
        "temperature": 0.9,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048
    }


def get_safety_settings():
    return [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
    ]


def create_model(model_name):
    return genai.GenerativeModel(model_name=model_name, generation_config=get_generation_config(),
                                 safety_settings=get_safety_settings())


def generate_response(model, prompt_parts, stream_response=False):
    model = create_model(model)
    print(model)
    print(prompt_parts)
    try:
        response = model.generate_content(prompt_parts, stream=stream_response)
        print(response)
        return response
    except Exception as e:
        logging.error(f"Error generating content: {e}")
        return None

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-l', '--log', default='ERROR', help='Set logging level')
    argparser.add_argument('-p', '--prompt', required=True, help='Prompt string')
    argparser.add_argument('-m', '--model', default="gemini-1.5-pro-latest", help='Model name')
    argparser.add_argument('-S', '--streamresponse', action='store_true', help='Stream response')
    args = argparser.parse_args()

    configure_logging(args.log)
    configure_api()

    model = create_model(args.model)
    prompt_parts = [args.prompt]  # Adjust as necessary for actual use case
    result = generate_response(model, prompt_parts, args.streamresponse)

    if result:
        logging.info(f"Result: {result}")
    else:
        logging.info("No result received or an error occurred.")
