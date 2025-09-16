from dotenv import load_dotenv
import os
import json

from azure_speech_subs import SpeechSynthesizer



if __name__ == "__main__":
    load_dotenv()

    with open("test/in/text.txt", "r") as f:
        text = f.read()
    voice = "zh-CN-YunjianNeural"
    split_characters = ["？", "。", "：", "，", "、", "”"]

    synthesizer = SpeechSynthesizer(os.getenv("AZURE_SPEECH_KEY"), os.getenv("AZURE_SPEECH_REGION"))

    synthesizer.generate_speech_with_subtitles(text, voice, "test/out", split_characters)