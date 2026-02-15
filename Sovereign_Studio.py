import streamlit as st
import whisper
import os
from streamlit_mic_recorder import mic_recorder
from pydub import AudioSegment, effects
from moviepy.video.VideoClip import ColorClip, TextClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sovereign Studio", page_icon="🎙️", layout="wide")
st.title("🎙️ Sovereign Studio")

# --- FIXED CORE FUNCTION ---
def process_audio(voice_path, music_path, music_volume, noise_reduction):
    # Load Voice
    voice = AudioSegment.from_file(voice_path)
    voice = effects.normalize(voice)
    
    if noise_reduction > 0:
        voice = voice.high_pass_filter(noise_reduction)
    
    # Check if background music exists and has size
    if os.path.exists(music_path) and os.path.getsize(music_path) > 0:
        try:
            bg = AudioSegment.from_file(music_path)
            # Loop music to match voice and apply volume
            bg_looped = bg.loop(duration=len(voice))
            bg_combined = bg_looped + music_volume
            # Overlay music onto voice
            final_mix = voice.overlay(bg_combined)
        except Exception as e:
            st.error(f"Music Error: {e}")
            final_mix = voice
    else:
        final_mix = voice
        
    output_path = "processed_audio.mp3"
    final_mix.export(output_path, format="mp3", bitrate="192k")
    return output_path

# --- FUNCTIONS FOR VIDEO ---
def create_video(audio_path, transcript):
    audio = AudioFileClip(audio_path)
    duration = min(audio.duration, 60)
    bg = ColorClip(size=(1080, 1920), color=(20, 20, 20)).set_duration(duration)
    txt = TextClip(
        text=transcript[:150] + "...", 
        font_size=70, 
        color='gold', 
        method='caption',
        size=(900, None)
    ).set_duration(duration).set_position('center')
    video = CompositeVideoClip([bg, txt]).set_audio(audio.subclip(0, duration))
    video_path = "promo_snippet.mp4"
    video.write_videofile(video_path, fps=24, codec="libx264", audio_codec="aac")
    return video_path

# --- APP TABS ---
tab1, tab2, tab3 = st.tabs(["1. Record Voice", "2. Mix & Transcribe", "3. Export Video"])

with tab1:
    st.subheader("🎤 Step 1: Capture Voice")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Option A: Live Record**")
        audio_record = mic_recorder(start_prompt="🔴 Start Recording", stop_prompt="⏹️ Stop", key='recorder')
        if audio_record:
            with open("raw_audio.wav", "wb") as f: f.write(audio_record['bytes'])
            st.success("Voice captured!")

    with col2:
        st.write("**Option B: Upload Voice**")
        uploaded_voice = st.file_uploader("Upload .mp3/.wav", type=["mp3", "wav"])
        if uploaded_voice:
            with open("raw_audio.wav", "wb") as f: f.write(uploaded_voice.getbuffer())
            st.success("Voice file uploaded!")

with tab2:
    if os.path.exists("raw_audio.wav"):
        st.subheader("🎚️ The Studio Mixer")
        
        st.write("🎵 **Add Background Music**")
        uploaded_bg = st.file_uploader("Upload music (e.g., 2face - Nobody)", type=["mp3"], key="bg_music")
        
        # Save the uploaded music to a persistent file
        if uploaded_bg:
            with open("background.mp3", "wb") as f:
                f.write(uploaded_bg.getbuffer())
            st.success("Music loaded into mixer!")
        
        col_vol, col_noise = st.columns(2)
        with col_vol:
            vol = st.slider("Music Volume", -40, -10, -25)
        with col_noise:
            noise = st.selectbox("Noise Cleanup", [0, 80, 150], format_func=lambda x: "None" if x==0 else "Standard")
        
        if st.button("✨ Mix & Transcribe"):
            if not os.path.exists("background.mp3") and uploaded_bg is None:
                st.warning("No music detected. Processing voice only...")
            
            with st.spinner("Mixing your track..."):
                final_audio = process_audio("raw_audio.wav", "background.mp3", vol, noise)
                
                # Transcription
                model = whisper.load_model("small")
                result = model.transcribe("raw_audio.wav", fp16=False, language='en')
                st.session_state['transcript'] = result['text']
                
                # Show the mixed result
                st.audio(final_audio)
        
        if 'transcript' in st.session_state:
            st.session_state['transcript'] = st.text_area("Correct errors:", value=st.session_state['transcript'], height=200)
    else:
        st.info("Record your voice in Tab 1 first.")

with tab3:
    if 'transcript' in st.session_state:
        st.subheader("🎬 Video Export")
        if st.button("Generate Video Snippet"):
            with st.spinner("Rendering..."):
                video_file = create_video("processed_audio.mp3", st.session_state['transcript'])
                st.video(video_file)
                with open(video_file, "rb") as f:
                    st.download_button("Download Video", f, "sovereign_promo.mp4")
    else:
        st.info("Process your audio in Tab 2 first.")
