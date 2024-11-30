import edge_tts
import streamlit as st
import asyncio
from base64 import b64encode
from utility.script.script_generator import generate_script
from utility.audio.audio_generator import generate_audio
from utility.captions.timed_captions_generator import generate_timed_captions
from utility.video.background_video_generator import generate_video_url
from utility.render.render_engine import get_output_media
from utility.video.video_search_query_generator import getVideoSearchQueriesTimed, merge_empty_intervals

# Function to display video in Streamlit
def display_video(video_path):
    try:
        with open(video_path, "rb") as video_file:
            video_bytes = video_file.read()
            video_url = f"data:video/mp4;base64,{b64encode(video_bytes).decode()}"
            st.video(video_url)
    except FileNotFoundError:
        st.error("Video file not found. Please try again.")

# Function to generate the video from the topic
async def generate_video_from_topic(topic, voice):
    SAMPLE_FILE_NAME = "audio_tts.wav"
    VIDEO_SERVER = "pexel"

    # Generate script
    response = generate_script(topic)
    if not response:
        st.error("Failed to generate script. Please try again.")
        return
    st.success("Script generated successfully!")
    st.write(f"*Generated Script:* {response}")

    # Generate audio
    st.info(f"Generating audio using voice: {voice}")
    await generate_audio(response, SAMPLE_FILE_NAME, voice)

    # Generate timed captions
    timed_captions = generate_timed_captions(SAMPLE_FILE_NAME)

    # Generate search terms and video URLs
    search_terms = getVideoSearchQueriesTimed(response, timed_captions)
    if search_terms:
        background_video_urls = generate_video_url(search_terms, VIDEO_SERVER)
        background_video_urls = merge_empty_intervals(background_video_urls)
    else:
        st.error("Failed to generate background video. Please try again.")
        return

    # Render final video
    if background_video_urls:
        output_video = get_output_media(SAMPLE_FILE_NAME, timed_captions, background_video_urls, VIDEO_SERVER)
        st.success("Video rendered successfully!")
        st.write("*Final Video:*")
        display_video(output_video)
    else:
        st.error("Failed to render video. Please try again.")

# Sidebar for "About" section
with st.sidebar:
    st.header("About")
  
    st.write("""
        **Script2Scene**:
        This tool generates a video from a given text topic. Here's how it works:
        1. **Script Generation**: The model creates a script based on the topic using AI.
        2. **Audio Generation**: Converts the script into speech using Edge TTS.
        3. **Captioning**: Generates timed captions for the audio.
        4. **Video Generation**: Creates a video by finding relevant background footage.
        5. **Rendering**: Combines audio, captions, and background video into the final output.
        """)

from PIL import Image
import streamlit as st

# Load and display the logo
logo_path = "/content/long_form_video_gen/kiran1.jpg"
logo = Image.open(logo_path)

# Create two columns: one for the logo and one for the title
col1, col2 = st.columns([1, 4])  # Adjust column proportions as needed
with col1:
    st.image(logo, use_container_width=True)  # Use the updated parameter
with col2:
    st.markdown("<h1 style='color: #4CAF50; margin: 0;'>Script2Scene</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #555; font-style: italic;'>Where Your Ideas Become Videos 🎬✨</h4>", unsafe_allow_html=True)


st.write("Enter a topic to generate a script and create a video!")

# User input
topic = st.text_input("Enter a topic:", placeholder="e.g., Fruits, AI, or Nature")

# Audio voice options
st.write("Select the voice settings:")
gender = st.radio("Select Gender:", ("Male", "Female"))
accent = st.selectbox("Select Accent:", ("British", "American"))

# Mapping gender and accent to Edge TTS voice names
voice_mapping = {
    ("Male", "British"): "en-GB-RyanNeural",
    ("Female", "British"): "en-GB-LibbyNeural",
    ("Male", "American"): "en-US-GuyNeural",
    ("Female", "American"): "en-US-JennyNeural",
}

try:
    voice = voice_mapping[(gender, accent)]
    st.write(f"Selected Voice: {voice}")  # Debug log for verification
except KeyError:
    st.error("Invalid voice selection. Please check your input.")
    voice = None

if st.button("Generate Video") and voice:
    if topic.strip():
        st.info("Processing your request. Please wait...")
        asyncio.run(generate_video_from_topic(topic, voice))
    else:
        st.error("Please enter a valid topic!") 
