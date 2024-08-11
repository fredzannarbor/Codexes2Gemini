import streamlit as st
from pathlib import Path
from google.cloud import texttospeech
import os

GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is not set.")
st.info(GOOGLE_API_KEY)

def generate_speech(input_text, speech_file_basename):
    """Generates speech from input text using Google Cloud Text-to-Speech API."""
    speech_file_path = Path("submission_video/audio", speech_file_basename + ".mp3")
    st.info(speech_file_path)

    credentials, project_id = default()
    client = texttospeech.TextToSpeechClient(credentials=credentials)

    # Instantiates a client
    client = texttospeech.TextToSpeechClient()

    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=input_text)

    # Build the voice request, select the language code ("en-US") and the SSML
    # voice gender ("neutral")
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    # Perform the text-to-speech request
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    # The response's audio_content is binary.
    with open(speech_file_path, "wb") as out:
        out.write(response.audio_content)

    st.success(f"Speech saved to {speech_file_path}")

def main():
    st.title("Google Cloud Text-to-Speech")

    input_text = st.text_area("Enter your text:", height=200)

    speech_file_basename = st.text_input("Basename for output file", help="we will append .mp3")

    if st.button("Generate Speech"):
        generate_speech(input_text, speech_file_basename)

if __name__ == "__main__":
    main()