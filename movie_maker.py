from moviepy.editor import *
import json
import requests
from io import BytesIO
from PIL import Image
import textwrap
import numpy as np

def download_image(url):
    """Download image from URL"""
    response = requests.get(url)
    return Image.open(BytesIO(response.content))

def create_reel(json_file="image_captions.json", output_file="output_reel.mp4"):
    """Create a video reel from images and captions"""
    
    # Load the JSON data
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Sort images by date_time if available
    images = data['images']
    images.sort(key=lambda x: x.get('metadata', {}).get('date_time') or '')
    
    clips = []
    duration_per_image = 5  # seconds per image
    transition_duration = 1  # seconds for smooth crossfade
    
    for image_data in images:
        try:
            # Download image from URL
            image_url = image_data['image_url']
            caption = image_data['insta_reel_caption']
            
            # Create image clip
            img = download_image(image_url)
            img_clip = ImageClip(np.array(img)).set_duration(duration_per_image)
            
            # Resize to Instagram reel dimensions (1080x1920)
            img_clip = img_clip.resize(height=1920)
            if img_clip.w > 1080:
                img_clip = img_clip.resize(width=1080)
            
            # Center the image
            img_clip = img_clip.set_position('center')
            
            # Create caption text clip
            if caption:
                # Wrap text to fit screen
                wrapped_text = textwrap.fill(caption, width=40)
                txt_clip = TextClip(
                    wrapped_text,
                    font='Comic-Sans-MS',  # Fun and playful font
                    fontsize=60,
                    color='white',
                    stroke_color='black',
                    stroke_width=2,
                    size=(1000, None),
                    method='caption'
                ).set_duration(duration_per_image)
                
                # Animate text: fade in and fade out
                txt_clip = txt_clip.fadein(0.5).fadeout(0.5)
                
                # Position text at bottom
                txt_clip = txt_clip.set_position(('center', 1500))
                
                # Composite image and text
                final_clip = CompositeVideoClip(
                    [img_clip, txt_clip],
                    size=(1080, 1920)
                )
            else:
                final_clip = img_clip
            
            # Add crossfade transition
            final_clip = final_clip.crossfadein(transition_duration)
            clips.append(final_clip)
            
        except Exception as e:
            print(f"Error processing image {image_data['file_name']}: {e}")
            continue
    
    # Concatenate all clips
    if clips:
        final_video = concatenate_videoclips(clips, method="compose", padding=-transition_duration)
        
        # Add background music (optional)
        try:
            audio = AudioFileClip("background_music.mp3").subclip(0, final_video.duration)
            final_video = final_video.set_audio(audio)
        except Exception as e:
            print(f"Background music error: {e}")
        
        # Write the final video
        final_video.write_videofile(
            output_file,
            fps=24,
            codec='libx264',
            audio_codec='aac'
        )
        print(f"Reel created successfully: {output_file}")
    else:
        print("No clips were created successfully")

if __name__ == "__main__":
    create_reel()
