import streamlit as st
import os
from orchestrator import VideoOrchestrator
from library_manager import LibraryManager

st.set_page_config(page_title="Dog Video AI", layout="wide")

def main():
    st.title("🐶 Dog Video AI Generator")
    st.markdown("Create viral YouTube Shorts about dogs with AI!")

    # Sidebar
    st.sidebar.header("Create New Video")
    prompt = st.sidebar.text_area("What is the video about?", height=150, 
                                  placeholder="E.g. 3 Secret Dog Meanings... \n[0:05] Hook...")
    
    generate_btn = st.sidebar.button("🎥 Generate Video", type="primary")

    # Main Content
    tab1, tab2 = st.tabs(["Current Video", "Library Gallery"])

    with tab1:
        if generate_btn and prompt:
            status_container = st.empty()
            log_container = st.container()
            
            logs = []
            def update_progress(msg):
                logs.append(msg)
                with log_container:
                    st.text(msg)
            
            with st.spinner("Agent is working..."):
                try:
                    orch = VideoOrchestrator()
                    result = orch.create_video(prompt, progress_callback=update_progress)
                    
                    st.success("Video Created Successfully!")
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        # Display video from Cloudinary if local is cleaned up
                        if result.get('local_path') and os.path.exists(result['local_path']):
                            st.video(result['local_path'])
                        elif result.get('cloudinary_url'):
                            st.video(result['cloudinary_url'])
                        else:
                            st.warning("Video processing complete but playback unavailable.")
                    with col2:
                        st.json(result['timeline'])
                        if result.get('cloudinary_url'):
                            st.markdown(f"**☁️ Cloudinary Link:** [View Online]({result['cloudinary_url']})")
                    
                except Exception as e:
                    st.error(f"Failed to generate video: {e}")

    with tab2:
        st.header("Video Library")
        lib = LibraryManager()
        videos = lib.get_all_videos()
        
        # Display in grid
        if not videos:
            st.info("No videos created yet.")
        else:
            # Sort by new
            videos = list(reversed(videos))
            for vid in videos:
                with st.expander(f"{vid['timestamp']} - {vid.get('prompt', '')[:50]}..."):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        # Try local first, fallback to Cloudinary
                        local_path = vid.get('local_path')
                        if local_path and os.path.exists(local_path):
                            st.video(local_path)
                        elif vid.get('cloudinary_url'):
                            st.video(vid['cloudinary_url'])
                        else:
                            st.warning("Video unavailable (local deleted, no cloud backup).")
                    with c2:
                         st.write(f"**ID:** {vid['id']}")
                         st.write(f"**Prompt:** {vid['prompt']}")
                         if vid.get('cloudinary_url'):
                             st.markdown(f"[Cloudinary Link]({vid['cloudinary_url']})")

if __name__ == "__main__":
    main()
