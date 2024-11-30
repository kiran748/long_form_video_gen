import edge_tts

# Function to generate audio with selected voice
async def generate_audio(text, output_filename, voice):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_filename)





