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
st.markdown("### *Produced by The Sovereign Investor*")

# --- FUNCTIONS ---
def process_audio(file_path):
    audio = AudioSegment.from_file(file_path)
    normalized_audio = effects.normalize(audio)
    output_path = "processed_audio.mp3"
    normalized_audio.export(output_path, format="mp3")
    return output_path

def create_video(audio_path, transcript):
    audio = AudioFileClip(audio_path)
    duration = min(audio.duration, 60)
    
    # Background: Sovereign Gold & Black theme
    bg = ColorClip(size=(1080, 1920), color=(20, 20, 20)).set_duration(duration)
    
    # Caption Overlay
    txt = TextClip(
        text=transcript[:120] + "...", 
        font_size=70, 
        color='gold', 
        method='caption',
        size=(900, None)
    ).set_duration(duration).set_position('center')
    
    video = CompositeVideoClip([bg, txt]).set_audio(audio.subclip(0, duration))
    video_path = "promo_snippet.mp4"
    video.write_videofile(video_path, fps=24, codec="libx264")
    return video_path

# --- APP TABS ---
st.divider()
tab1, tab2, tab3 = st.tabs(["1. Record or Upload", "2. Transcribe & Edit", "3. Export Snippet"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Live Studio")
        audio_record = mic_recorder(
            start_prompt="🔴 Start Recording",
            stop_prompt="⏹️ Stop Recording",
            key='recorder'
        )
        if audio_record:
            with open("raw_audio.wav", "wb") as f:
                f.write(audio_record['bytes'])
            st.success("Recording captured!")
            st.audio(audio_record['bytes'])

    with col2:
        st.subheader("Upload from Phone")
        uploaded_file = st.file_uploader("Drop a .wav or .mp3 here", type=["wav", "mp3"])
        if uploaded_file:
            with open("raw_audio.wav", "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("File uploaded!")

with tab2:
    if os.path.exists("raw_audio.wav"):
        if st.button("🔍 Clean & Transcribe"):
            with st.spinner("AI is listening..."):
                clean_path = process_audio("raw_audio.wav")
                model = whisper.load_model("base")
                result = model.transcribe("raw_audio.wav")
                st.session_state['transcript'] = result['text']
            
            st.audio("processed_audio.mp3")
            st.text_area("Edit Transcript:", value=st.session_state['transcript'], key="edited_text", height=200)
    else:
        st.info("Record something in Step 1 first.")

with tab3:
    if 'transcript' in st.session_state:
        if st.button("🎬 Generate MP4"):
            with st.spinner("Rendering Video..."):
                video_file = create_video("processed_audio.mp3", st.session_state.get('edited_text', st.session_state['transcript']))
                st.video(video_file)
                with open(video_file, "rb") as f:
                    st.download_button("Download Snippet", f, "sovereign_promo.mp4")