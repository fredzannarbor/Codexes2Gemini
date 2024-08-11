from pathlib import Path
import argparse
import openai

def main():
    parser = argparse.ArgumentParser(description="Generate speech from text using OpenAI's TTS API.")
    parser.add_argument("--input", "-i", type=str, required=True, help="Text to convert to speech.")
    parser.add_argument("--output", "-o", type=str, default="speech.mp3", help="Output file name.")
    args = parser.parse_args()

    speech_file_path = Path(args.output)
    response = openai.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=args.input
    )

    with open(speech_file_path, "wb") as f:
        f.write(response.content)

    print(f"Speech saved to {speech_file_path}")

if __name__ == "__main__":
    main()