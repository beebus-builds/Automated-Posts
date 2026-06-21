import os
from moviepy.editor import ImageClip, ColorClip, CompositeVideoClip, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.video.fx.all import resize

def generate_video(image_path, output_path, caption):
    """
    Generates a high-energy vertical Reel from a static image.
    - Aspect Ratio: 1080x1920
    - Effect: Ken Burns (Slow Zoom)
    - Audio: Stadium background noise
    """
    # 1. Load the base image (1080x1080)
    # Since our image is square, we'll place it in a 1080x1920 canvas
    base_img = ImageClip(image_path).set_duration(7)
    
    # 2. Create the Vertical Background (1080x1920)
    # We create a black background and place the square image in the center
    bg = ColorClip(size=(1080, 1920), color=(10, 10, 15)).set_duration(7)
    
    # 3. Implement "Ken Burns" Effect (Slow Zoom)
    # We animate the scale from 1.0 to 1.2 over 7 seconds
    def zoom_effect(t):
        return 1 + 0.03 * t  # Zoom in by 3% per second
    
    # Note: MoviePy's resize can be used with a function for animation
    zoomed_img = base_img.resize(zoom_effect).set_position('center')
    
    # 4. Add Animated Caption (Simple Fade-in)
    # In a real env, we'd use a fancy font. Here we use a basic TextClip.
    txt_clip = TextClip(
        caption, 
        fontsize=70, 
        color='white', 
        font='Arial-Bold', 
        method='caption', 
        size=(900, None)
    ).set_start(1).set_duration(6).set_position(('center', 1400)).crossfadein(1)
    
    # 5. Add Background Audio (Stadium Noise)
    # We use a placeholder for the audio path. The user should provide a 'stadium.mp3'
    audio_path = "src/static/audio/stadium_crowd.mp3"
    if os.path.exists(audio_path):
        audio = AudioFileClip(audio_path).subclip(0, 7)
        final_video = CompositeVideoClip([bg, zoomed_img, txt_clip]).set_audio(audio)
    else:
        final_video = CompositeVideoClip([bg, zoomed_img, txt_clip])

    # 6. Export as MP4
    final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    
    return output_path
