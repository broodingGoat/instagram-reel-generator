# Instagram Reel Generator

Automatically generate Instagram Reels from images using AI-powered captions and analysis.

## Features
- AI-powered image analysis using OpenAI's Vision API
- Extracts image metadata (GPS, datetime)
- Generates engaging Instagram captions
- Creates video reels with transitions and text overlays
- Background music support

## Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your API keys
4. Place images in `images/` folder
5. (Optional) Add background music to `background_music/` folder
6. Requires Open AI API Keys and ngrok URL, to access locally stored images

## Usage
1. Run image analysis: `python image_analyzer.py`
2. Create video reel: `python movie_maker.py`

## Output
- `image_captions.json`: Analysis and captions for each image
- `output_reel.mp4`: Generated Instagram reel 

## Inspiration & Work
- Post meditation ideation by @arjitby 🧘🧘
- Generated entirely using OpenAI APIs (50 requests, 40k input tokens)and Cursor IDE (40/500 requests). Paid subscription + $0.22 for inital commit
