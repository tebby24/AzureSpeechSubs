# AzureSpeechSubs
AI text-to-speech is getting pretty good. There are lots of available APIs to choose from, but almost no good ways to get a matching SRT transcript of your synthasized speech. This project attempts to solve this problem for the Microsoft Azure's TTS api, since it at least provides word level timestamping. 

## Usage

```python
from azure_speech_subs.synthesizer import SpeechSynthesizer

synth = SpeechSynthesizer(azure_speech_key="YOUR_KEY", azure_speech_region="YOUR_REGION")
result = synth.generate_speech_with_subtitles(
    text="Hello world. This is a test.",
    voice="en-US-JennyNeural",
    output_directory="./output",
    split_characters=[".", ",", "?", "\""]
)
print(result)  # {'audio': ..., 'words': ..., 'transcript': ...}
```

This will generate:
- `audio.wav`: synthesized speech
- `words.json`: word-level timing info
- `transcript.srt`: subtitle file

You can get an API key and region from the Azure Portal by creating a Speech resource. 
Find voices by browsing the [Azure Voice Gallery](https://speech.microsoft.com/portal/voicegallery).

### Subtitle Splitting

The Azure TTS api only provides word level timestamps, so we have to combine them into larger subtitles based on the split_characters provided to generate_speech_with_subtitles. We only split if the last character in the word level timestamp appears in split_characters. This way we avoid splitting on opening quotation marks.  

### Related Projects
https://github.com/hesic73/SpeechSynthSubs