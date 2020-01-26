## Voice Sizer

Simple sizing via vocal prompts. Can be used with user audio mic or typed responses.

Uses Bing Speech API for vocals, Bing Maps for Address, and Microsoft's LUIS.ai for language understanding.

Connects to Google Sheets for UW.

Uses really crappy pygame mixer for audio - apologies for the weird, usually not working prompt sound!

### Install

`pip install requirements.txt`

`python create_sizing.py`

API keys are stored at the bottom of `create_sizing.py`

First time run, google will open a browser window for OAuth to the google sheet

### Not quite completed

- Address saves to a single cell in google sheet instead of being split
- Only FHA quote is returned for now

