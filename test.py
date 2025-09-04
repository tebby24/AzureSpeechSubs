from dotenv import load_dotenv
import os

from azure_speech_subs.synthesizer import SpeechSynthesizer



if __name__ == "__main__":
    load_dotenv()

    with open("test/in/text.txt", "r") as f:
        text = f.read()
    voice = "zh-CN-YunjianNeural"

    synthesizer = SpeechSynthesizer(os.getenv("AZURE_SPEECH_KEY"), os.getenv("AZURE_SPEECH_REGION"))

    synthesizer.synthesize_speech(text, voice, "test/out")