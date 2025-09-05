import os
import requests
import time
import uuid
import zipfile
import json
import srt
from datetime import timedelta
import shutil

class SpeechSynthesizer:
    def __init__(self, azure_speech_key, azure_speech_region):
        self.azure_speech_key = azure_speech_key
        self.azure_speech_region = azure_speech_region
        self.base_url = f"https://{azure_speech_region}.api.cognitive.microsoft.com"

    def synthesize_speech(self, text, voice, output_directory):
        """
        Synthesize speech using Azure Batch Synthesis API
        
        Args:
            text (str): Text to synthesize
            voice (str): Voice name (e.g., 'en-US-JennyNeural')
            output_directory (str): Directory to save output files
            
        Returns:
            dict: Contains paths to generated audio and boundary files
        """
        # Create unique synthesis ID
        synthesis_id = str(uuid.uuid4())
        
        # Ensure output directory exists
        os.makedirs(output_directory, exist_ok=True)
        
        # Submit batch synthesis request
        synthesis_url = f"{self.base_url}/texttospeech/batchsyntheses/{synthesis_id}?api-version=2024-04-01"
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.azure_speech_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputKind": "PlainText",
            "synthesisConfig": {
                "voice": voice
            },
            "inputs": [
                {
                    "content": text
                }
            ],
            "properties": {
                "outputFormat": "riff-24khz-16bit-mono-pcm",
                "wordBoundaryEnabled": True,
                "sentenceBoundaryEnabled": False,
                "concatenateResult": False,
                "decompressOutputFiles": False
            }
        }
        
        # Submit the request
        response = requests.put(synthesis_url, headers=headers, json=payload)
        response.raise_for_status()
        
        # Poll for completion
        while True:
            status_response = requests.get(synthesis_url, headers=headers)
            status_response.raise_for_status()
            status_data = status_response.json()
            
            if status_data["status"] == "Succeeded":
                break
            elif status_data["status"] == "Failed":
                raise Exception(f"Synthesis failed: {status_data}")
            
            # Wait before polling again
            time.sleep(5)
        
        # Download results
        results_url = status_data["outputs"]["result"]
        results_response = requests.get(results_url, headers={"Ocp-Apim-Subscription-Key": self.azure_speech_key})
        results_response.raise_for_status()
        
        # Save and extract ZIP file
        zip_path = os.path.join(output_directory, f"{synthesis_id}_results.zip")
        with open(zip_path, "wb") as f:
            f.write(results_response.content)
        
        # Extract files
        extracted_files = {}
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for filename in zip_ref.namelist():
                if filename.endswith('.wav'):
                    zip_ref.extract(filename, output_directory)
                    extracted_files['audio'] = os.path.join(output_directory, filename)
                elif filename.endswith('.word.json'):
                    zip_ref.extract(filename, output_directory)
                    extracted_files['word_boundaries'] = os.path.join(output_directory, filename)
                # Skip summary.json and other unnecessary files
        
        # Clean up ZIP file
        os.remove(zip_path)
        
        # Clean up the batch synthesis job
        delete_response = requests.delete(synthesis_url, headers=headers)
        # Note: We don't raise_for_status() here as cleanup failure shouldn't break the main flow
        
        return extracted_files

    def build_groups(self, word_boundaries, split_characters):
        groups = []        
        start_time = None

        current_sub = ""
        for token in word_boundaries:
            text = token.get("Text") or token.get("text")
            offset = token.get("AudioOffset") or token.get("audiooffset")
            duration = token.get("Duration") or token.get("duration")

            if start_time is None:
                start_time = offset

            current_sub += text

            if text and text[-1] in split_characters:
                group = {
                    "text": current_sub.strip(),
                    "start": start_time,
                    "end": offset + duration
                }
                groups.append(group)

                current_sub = ""
                start_time = None
        
        # Handle any remaining text that doesn't end with split characters
        if current_sub.strip() and start_time is not None:
            group = {
                "text": current_sub.strip(),
                "start": start_time,
                "end": offset + duration if 'offset' in locals() and 'duration' in locals() else start_time + 1000
            }
            groups.append(group)
            
        return groups
            
    def save_subs(self, groups, srt_filepath):
        subs = []
        for i, group in enumerate(groups):
            start = timedelta(milliseconds=group["start"])
            end = timedelta(milliseconds=group["end"])
            content = group["text"]

            sub = srt.Subtitle(index=i+1, start=start, end=end, content=content)
            subs.append(sub)

        srt_content = srt.compose(subs)

        with open(srt_filepath, "w", encoding="utf-8") as f:
            f.write(srt_content)

    def generate_speech_with_subtitles(self, text, voice, output_directory, split_characters=".!?"):
        """
        Complete pipeline to generate speech with subtitles
        
        Args:
            text (str): Text to synthesize
            voice (str): Voice name (e.g., 'en-US-JennyNeural')
            output_directory (str): Directory to save output files
            split_characters (str): Characters to split subtitles on
            
        Returns:
            dict: Contains paths to audio.wav, words.json, and transcript.srt
        """
        try:
            # Step 1: Synthesize speech and get raw files
            raw_files = self.synthesize_speech(text, voice, output_directory)
            
            # Step 2: Load word boundaries
            with open(raw_files['word_boundaries'], 'r', encoding='utf-8') as f:
                word_boundaries = json.load(f)
            
            # Step 3: Build subtitle groups
            groups = self.build_groups(word_boundaries, split_characters)
            
            # Step 4: Define final output paths
            final_audio_path = os.path.join(output_directory, "audio.wav")
            final_words_path = os.path.join(output_directory, "words.json")
            final_srt_path = os.path.join(output_directory, "transcript.srt")
            
            # Step 5: Rename audio file
            if 'audio' in raw_files:
                shutil.move(raw_files['audio'], final_audio_path)
            
            # Step 6: Copy and rename word boundaries file
            if 'word_boundaries' in raw_files:
                shutil.copy2(raw_files['word_boundaries'], final_words_path)
                os.remove(raw_files['word_boundaries'])
            
            # Step 7: Generate and save SRT file
            self.save_subs(groups, final_srt_path)
            
            # No need to clean up summary.json since we don't extract it
            
            return {
                'audio': final_audio_path,
                'words': final_words_path,
                'transcript': final_srt_path
            }
            
        except Exception as e:
            # Clean up any partial files on error
            for filename in ['audio.wav', 'words.json', 'transcript.srt']:
                filepath = os.path.join(output_directory, filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
            raise e

