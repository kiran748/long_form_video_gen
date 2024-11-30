import os
import requests
from diffusers import StableDiffusionPipeline
import cv2
import numpy as np

# Utility functions
from utility.utils import log_response, LOG_TYPE_PEXEL

# Environment variable for Pexels API Key
PEXELS_API_KEY = os.environ.get('PEXELS_KEY')

# Initialize Stable Diffusion
def initialize_stable_diffusion(model_name="CompVis/stable-diffusion-v1-4", device="cpu"):
    print("Initializing Stable Diffusion model...")
    pipeline = StableDiffusionPipeline.from_pretrained(model_name)
    pipeline.to(device)
    return pipeline

stable_diffusion_pipeline = initialize_stable_diffusion()

# Function to search videos on Pexels
def search_videos(query_string, orientation_landscape=True):
    url = "https://api.pexels.com/videos/search"
    headers = {
        "Authorization": PEXELS_API_KEY,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    params = {
        "query": query_string,
        "orientation": "landscape" if orientation_landscape else "portrait",
        "per_page": 15
    }

    response = requests.get(url, headers=headers, params=params)
    json_data = response.json()
    log_response(LOG_TYPE_PEXEL, query_string, response.json())
    return json_data

# Function to get the best video from Pexels
def getBestVideo(query_string, orientation_landscape=True, used_vids=[]):
    vids = search_videos(query_string, orientation_landscape)
    videos = vids['videos']  # Extract the videos list from JSON

    # Filter and extract videos
    if orientation_landscape:
        filtered_videos = [
            video for video in videos 
            if video['width'] >= 1920 and video['height'] >= 1080 and video['width'] / video['height'] == 16 / 9
        ]
    else:
        filtered_videos = [
            video for video in videos 
            if video['width'] >= 1080 and video['height'] >= 1920 and video['height'] / video['width'] == 16 / 9
        ]

    # Sort by duration close to 15 seconds
    sorted_videos = sorted(filtered_videos, key=lambda x: abs(15 - int(x['duration'])))

    # Extract video URLs
    for video in sorted_videos:
        for video_file in video['video_files']:
            if orientation_landscape:
                if video_file['width'] == 1920 and video_file['height'] == 1080:
                    if not (video_file['link'].split('.hd')[0] in used_vids):
                        return video_file['link']
            else:
                if video_file['width'] == 1080 and video_file['height'] == 1920:
                    if not (video_file['link'].split('.hd')[0] in used_vids):
                        return video_file['link']
    print("No suitable links found for this round of search with query:", query_string)
    return None

# Generate image using Stable Diffusion
def generate_image_with_stable_diffusion(prompt, pipeline, resolution=(1920, 1080)):
    print(f"Generating image for prompt: {prompt}")
    image = pipeline(prompt).images[0]
    image = image.resize(resolution)  # Resize to desired resolution
    return np.array(image)  # Convert to numpy array

# Save frames as video
def save_frames_as_video(frames, output_path, fps=30):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    height, width, _ = frames[0].shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    for frame in frames:
        video_writer.write(frame)
    video_writer.release()

# Fallback for Stable Diffusion
def get_images_for_video(timed_video_searches):
    generated_videos = []
    for (t1, t2), search_terms in timed_video_searches:
        frames = []
        for query in search_terms:
            try:
                # Generate frames using Stable Diffusion
                frame = generate_image_with_stable_diffusion(query, stable_diffusion_pipeline)
                frames.append(frame)
            except Exception as e:
                print(f"Error generating image for query '{query}': {e}")

        if frames:
            # Save frames as a video
            video_path = f"generated_videos/video_{t1}_{t2}.mp4"
            save_frames_as_video(frames, video_path)
            generated_videos.append([[t1, t2], video_path])
        else:
            generated_videos.append([[t1, t2], None])
    return generated_videos

# Main function to generate video URLs
def generate_video_url(timed_video_searches, video_server):
    timed_video_urls = []
    used_links = []

    if video_server == "pexel":
        for (t1, t2), search_terms in timed_video_searches:
            url = ""
            for query in search_terms:
                url = getBestVideo(query, orientation_landscape=True, used_vids=used_links)
                if url:
                    used_links.append(url.split('.hd')[0])
                    break

            # Fallback to Stable Diffusion
            if not url:
                print(f"No suitable Pexels video found for [{t1}-{t2}]. Using Stable Diffusion.")
                frames = []
                for query in search_terms:
                    try:
                        frame = generate_image_with_stable_diffusion(query, stable_diffusion_pipeline)
                        frames.append(frame)
                    except Exception as e:
                        print(f"Error generating image for query '{query}': {e}")

                if frames:
                    video_path = f"generated_videos/video_{t1}_{t2}.mp4"
                    save_frames_as_video(frames, video_path)
                    url = video_path
            timed_video_urls.append([[t1, t2], url])

    elif video_server == "stable_diffusion":
        timed_video_urls = get_images_for_video(timed_video_searches)

    return timed_video_urls
