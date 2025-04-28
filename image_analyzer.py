from openai import OpenAI
import piexif
from PIL import Image
import base64
import os
from pathlib import Path
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Your ngrok base URL
ngrok_url = os.getenv('NGROK_URL')

# Local path to read metadata
local_folder_path = "/Users/sm/story-gen/images/Photos-001/"

# 1. Extract Metadata
def extract_metadata(img_path):
    try:
        exif_data = piexif.load(img_path)
        gps_data = exif_data.get('GPS', {})
        date_time = exif_data.get('Exif', {}).get(piexif.ExifIFD.DateTimeOriginal)
        
        # Parse GPS coordinates if available
        if gps_data:
            gps_latitude = gps_data.get(piexif.GPSIFD.GPSLatitude)
            gps_latitude_ref = gps_data.get(piexif.GPSIFD.GPSLatitudeRef)
            gps_longitude = gps_data.get(piexif.GPSIFD.GPSLongitude)
            gps_longitude_ref = gps_data.get(piexif.GPSIFD.GPSLongitudeRef)

            def dms_to_decimal(dms, ref):
                degrees = dms[0][0] / dms[0][1]
                minutes = dms[1][0] / dms[1][1]
                seconds = dms[2][0] / dms[2][1]
                decimal = degrees + minutes/60 + seconds/3600
                if ref in [b'S', b'W']:
                    decimal = -decimal
                return decimal

            lat = dms_to_decimal(gps_latitude, gps_latitude_ref)
            lon = dms_to_decimal(gps_longitude, gps_longitude_ref)
        else:
            lat, lon = None, None

        return {
            "date_time": date_time.decode() if date_time else None,
            "latitude": lat,
            "longitude": lon
        }
    except Exception as e:
        print(f"Metadata extraction failed for {img_path}: {e}")
        return {}

def analyze_image(file_name, metadata):
    image_url = ngrok_url + file_name
    
    # Build Prompt Dynamically
    prompt_parts = [
        "For this image, provide:\n"
        "1. A detailed description\n"
        "2. Location guess based on the image\n"
        "3. Start with 'Instagram Reel Caption:' followed by a catchy caption with relevant hashtags"
    ]

    if metadata.get("date_time"):
        prompt_parts.append(f"This photo was taken on {metadata['date_time']}.")

    if metadata.get("latitude") and metadata.get("longitude"):
        prompt_parts.append(f"The location coordinates are Latitude {metadata['latitude']}, Longitude {metadata['longitude']}.")

    full_prompt = " ".join(prompt_parts)

    print(f"\nProcessing image: {file_name}")
    print("Prompt:", full_prompt)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": full_prompt},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }
            ],
            max_tokens=400,
        )
        
        return {
            "file_name": file_name,
            "metadata": metadata,
            "analysis": {
                "description": response.choices[0].message.content,
                "insta_reel_caption": extract_insta_caption(response.choices[0].message.content)
            }
        }
    except Exception as e:
        print(f"API call failed for {file_name}: {e}")
        return {
            "file_name": file_name,
            "metadata": metadata,
            "error": str(e)
        }

def extract_insta_caption(content):
    """Extract Instagram caption from the full response"""
    # Look for numbered Instagram Reel Caption section
    if "3. **Instagram Reel Caption**:" in content:
        parts = content.split("3. **Instagram Reel Caption**:")
        if len(parts) > 1:
            caption = parts[1].strip()
            # Clean up any remaining markdown and quotes
            caption = caption.replace('*', '').replace('\"', '').strip()
            # Get only the first paragraph
            caption = caption.split('\n\n')[0].strip()
            return caption

    # Try other variations
    variations = [
        "**Instagram Reel Caption**:",
        "Instagram Reel Caption:",
        "3. Instagram Reel Caption:"
    ]
    
    for marker in variations:
        if marker in content:
            parts = content.split(marker)
            if len(parts) > 1:
                caption = parts[1].strip()
                caption = caption.replace('*', '').replace('\"', '').strip()
                caption = caption.split('\n\n')[0].strip()
                return caption
    
    # If no caption found, return None instead of last section
    return None

def process_folder():
    results = []
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    
    for file_name in os.listdir(local_folder_path):
        if file_name.lower().endswith(image_extensions):
            img_path = os.path.join(local_folder_path, file_name)
            metadata = extract_metadata(img_path)
            result = analyze_image(file_name, metadata)
            results.append(result)
            
            # Save results after each image (to prevent data loss)
            save_results(results)
    
    return results

def save_results(results):
    """Save results to a JSON file"""
    output_file = "image_captions.json"
    formatted_results = {
        "generated_at": datetime.now().isoformat(),
        "ngrok_base_url": ngrok_url,  # Adding base URL for reference
        "images": [
            {
                "file_name": r["file_name"],
                "image_url": ngrok_url + r["file_name"],  # Adding the full image URL
                "description": r["analysis"]["description"] if "analysis" in r else None,
                "insta_reel_caption": r["analysis"]["insta_reel_caption"] if "analysis" in r else None,
                "metadata": r["metadata"],
                "error": r.get("error")
            }
            for r in results
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    print(f"Processing images in folder: {local_folder_path}")
    results = process_folder()
    
    # Print results
    for result in results:
        print("\n-----------------------------------")
        print(f"File: {result['file_name']}")
        print(f"Metadata: {result['metadata']}")
        if 'analysis' in result:
            print(f"Description: {result['analysis']['description']}")
            print(f"Instagram Reel Caption: {result['analysis']['insta_reel_caption']}")
        if 'error' in result:
            print(f"Error: {result['error']}")
