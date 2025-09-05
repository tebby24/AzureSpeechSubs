from dotenv import load_dotenv
import os
import json

from azure_speech_subs.synthesizer import SpeechSynthesizer



if __name__ == "__main__":
    load_dotenv()

    with open("test/in/text.txt", "r") as f:
        text = f.read()
    voice = "zh-CN-YunjianNeural"

    synthesizer = SpeechSynthesizer(os.getenv("AZURE_SPEECH_KEY"), os.getenv("AZURE_SPEECH_REGION"))

    # synthesizer.synthesize_speech(text, voice, "test/out")

    with open("test/out/0001.word.json", "r") as f:
        word_boundaries = json.load(f)

    split_characters = ["？", "。", "：", "，", "、", "”"]

    groups = synthesizer.build_groups(word_boundaries, split_characters)
    [print(group) for group in groups]

    synthesizer.save_subs(groups, "test/out/srt.srt")