import os
import requests
import time
import uuid
import zipfile
import json

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
            zip_ref.extractall(output_directory)
            for filename in zip_ref.namelist():
                if filename.endswith('.wav'):
                    extracted_files['audio'] = os.path.join(output_directory, filename)
                elif filename.endswith('.word.json'):
                    extracted_files['word_boundaries'] = os.path.join(output_directory, filename)
                elif filename == 'summary.json':
                    extracted_files['summary'] = os.path.join(output_directory, filename)
        
        # Clean up ZIP file
        os.remove(zip_path)
        
        # Clean up the batch synthesis job
        delete_response = requests.delete(synthesis_url, headers=headers)
        # Note: We don't raise_for_status() here as cleanup failure shouldn't break the main flow
        
        return extracted_files

