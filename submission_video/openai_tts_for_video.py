import streamlit as st
from pathlib import Path
import openai

def generate_speech(input_text, speech_file_basename):
    """Generates speech from input text using OpenAI's TTS API."""
    speech_file_path = Path("submission_video/audio", speech_file_basename + ".mp3")
    st.info(speech_file_path)
    response = openai.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=input_text
    )

    with open(speech_file_path, "wb") as f:
        f.write(response.content)

    st.success(f"Speech saved to {speech_file_path}")

def main():
    st.title("OpenAI Text-to-Speech")

    input_text = st.text_area("Enter your text:", height=200)

    speech_file_basename = st.text_input("Basename for output file", help="we will append .mp3")

    if st.button("Generate Speech"):
        generate_speech(input_text, speech_file_basename)




if __name__ == "__main__":
    main()