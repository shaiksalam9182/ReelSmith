import streamlit as st
import os
import config
import time
from search_engine import load_memory, search_video
from modules import editor

# Page Config
st.set_page_config(page_title="ReelSmith: AI Video Agent", layout="wide")

# Title & CSS
st.title("🎬 ReelSmith: The AI Film Editor")
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'db' not in st.session_state:
    with st.spinner("🧠 Loading AI Memory Bank..."):
        st.session_state['db'] = load_memory("reelsmith_memory.json")
        st.success(f"Loaded {len(st.session_state['db'])} scenes from memory.")

# Sidebar - Controls
with st.sidebar:
    st.header("⚙️ Settings")
    top_k = st.slider("Max Clips to Retrieve", 1, 5, 3)
    st.info("Current Movie: Night of the Living Dead")

# Main Interface
query = st.text_input("🗣️ Describe the scene you want to find:", placeholder="e.g., A truck exploding in flames...")

if query:
    st.divider()
    st.subheader(f"🔎 Analyzing movie for: '{query}'...")
    
    # Run Search
    found_clips = search_video(query, st.session_state['db'], top_k=top_k)
    
    # Create Columns for Results
    cols = st.columns(top_k)
    
    selected_clips = []
    
    for i, clip_data in enumerate(found_clips):
        # We need to map the "clean" clip data back to the original shot for details if needed
        # But search_video returns the ready-to-cut dict.
        # Let's slightly modify logic to display details.
        
        with cols[i]:
            st.markdown(f"**Match #{i+1}**")
            st.code(f"{clip_data['start_seconds']:.2f}s -> {clip_data['start_seconds']+clip_data['duration']:.2f}s")
            st.caption("Ready to render")
            
    # "Magic" Button
    if st.button("✨ GENERATE VIDEO HIGHLIGHT REEL"):
        with st.status("🎬 Rendering video... Please wait...", expanded=True) as status:
            st.write("✂️ Cutting scenes from raw footage...")
            # Generate the file
            output_file = "streamlit_output.mp4"
            editor.create_highlight_reel(config.LOCAL_VIDEO_PATH, found_clips, output_file)
            st.write("✅ Stitching complete!")
            status.update(label="Video Ready!", state="complete", expanded=False)
            
        # Display Video Player
        st.divider()
        st.video(output_file)
        
        # Download Button
        with open(output_file, "rb") as file:
            btn = st.download_button(
                label="📥 Download Video",
                data=file,
                file_name="reelsmith_highlight.mp4",
                mime="video/mp4"
            )