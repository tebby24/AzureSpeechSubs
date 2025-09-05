from setuptools import setup, find_packages

setup(
    name="azure-speech-subs",
    packages=find_packages(), 
    install_requires=[
        "srt",
        "requests",
        "python-dotenv"
    ],
    author="Teddy Gonyea",
    description="A tool to generate speech with synchronized subtitles using Azure Cognitive Services.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/tebby24/AzureSpeechSubs",
)