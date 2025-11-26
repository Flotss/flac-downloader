"""
Dreamlight - FLAC Downloader Manager
A beautiful Streamlit interface for managing your music downloads.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.database import get_database
from src.config import settings


# ============ Page Configuration ============
st.set_page_config(
    page_title="Dreamlight - FLAC Downloader",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ Custom CSS ============
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --success-color: #22c55e;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --background-dark: #0f172a;
        --card-background: #1e293b;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
        padding: 2rem;
        border-radius: 1rem;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(99, 102, 241, 0.3);
    }

    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }

    .main-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }

    /* Stats cards */
    .stat-card {
        background: linear-gradient(145deg, #1e293b 0%, #334155 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid rgba(99, 102, 241, 0.2);
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(99, 102, 241, 0.3);
    }

    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .stat-label {
        color: #94a3b8;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.5rem;
    }

    /* Table styling */
    .stDataFrame {
        border-radius: 0.75rem;
        overflow: hidden;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border: none;
        border-radius: 0.5rem;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
    }

    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }

    .status-pending {
        background: rgba(245, 158, 11, 0.2);
        color: #f59e0b;
    }

    .status-downloaded {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
    }

    .status-error {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }

    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .animate-fade-in {
        animation: fadeIn 0.5s ease-out;
    }

    /* Card containers */
    .content-card {
        background: linear-gradient(145deg, #1e293b 0%, #334155 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(99, 102, 241, 0.1);
    }

    /* Track item */
    .track-item {
        display: flex;
        align-items: center;
        padding: 1rem;
        background: rgba(15, 23, 42, 0.5);
        border-radius: 0.75rem;
        margin-bottom: 0.5rem;
        border: 1px solid rgba(99, 102, 241, 0.1);
        transition: all 0.2s ease;
    }

    .track-item:hover {
        background: rgba(99, 102, 241, 0.1);
        border-color: rgba(99, 102, 241, 0.3);
    }

    /* Progress bar custom */
    .progress-container {
        background: rgba(99, 102, 241, 0.1);
        border-radius: 9999px;
        height: 8px;
        overflow: hidden;
    }

    .progress-bar {
        background: linear-gradient(90deg, #6366f1, #a855f7);
        height: 100%;
        border-radius: 9999px;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)


# ============ Initialize Database ============
@st.cache_resource
def init_database():
    """Initialize and cache the database connection."""
    return get_database()


db = init_database()


# ============ Helper Functions ============
def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes is None:
        return "N/A"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_datetime(dt_str) -> str:
    """Format datetime string to readable format."""
    if dt_str is None:
        return "N/A"
    try:
        if isinstance(dt_str, str):
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        else:
            dt = dt_str
        return dt.strftime("%d %b %Y, %H:%M")
    except Exception:
        return str(dt_str)


def get_status_emoji(status: str) -> str:
    """Get emoji for track status."""
    status_map = {
        'pending': '⏳',
        'downloading': '⬇️',
        'downloaded': '✅',
        'error': '❌'
    }
    return status_map.get(status, '❓')


# ============ Sidebar Navigation ============
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem;">
        <h2 style="color: #6366f1; margin: 0;">🎵 Dreamlight</h2>
        <p style="color: #94a3b8; font-size: 0.85rem;">FLAC Downloader Manager</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Navigation
    page = st.radio(
        "Navigation",
        ["🏠 Dashboard", "📋 Playlists", "🎵 Tracks", "📥 Downloads", "⚠️ Errors", "⚙️ Settings"],
        label_visibility="collapsed"
    )

    st.divider()

    # Quick stats
    stats = db.get_dashboard_stats()
    st.markdown(f"""
    <div style="padding: 0.5rem;">
        <p style="color: #94a3b8; font-size: 0.75rem; margin-bottom: 0.5rem;">QUICK STATS</p>
        <p style="color: white; margin: 0.25rem 0;">📋 {stats['playlists']} Playlists</p>
        <p style="color: white; margin: 0.25rem 0;">📥 {stats['total_downloads']} Downloads</p>
        <p style="color: white; margin: 0.25rem 0;">⚠️ {stats['errors_cached']} Errors</p>
    </div>
    """, unsafe_allow_html=True)


# ============ Page Content ============

if page == "🏠 Dashboard":
    # Header
    st.markdown("""
    <div class="main-header animate-fade-in">
        <h1>🎵 Dreamlight Dashboard</h1>
        <p>Manage your FLAC music library with ease</p>
    </div>
    """, unsafe_allow_html=True)

    # Stats row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="stat-card animate-fade-in">
            <div class="stat-number">{stats['playlists']}</div>
            <div class="stat-label">📋 Playlists</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-card animate-fade-in">
            <div class="stat-number">{stats['total_downloads']}</div>
            <div class="stat-label">📥 Downloads</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="stat-card animate-fade-in">
            <div class="stat-number">{stats['tracks_pending']}</div>
            <div class="stat-label">⏳ Pending</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="stat-card animate-fade-in">
            <div class="stat-number">{stats['errors_cached']}</div>
            <div class="stat-label">⚠️ Errors</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Two columns for recent activity
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📥 Recent Downloads")
        recent_downloads = db.get_downloads(limit=5)
        if recent_downloads:
            for download in recent_downloads:
                st.markdown(f"""
                <div class="track-item">
                    <div style="flex: 1;">
                        <strong style="color: white;">{download['title'][:40]}</strong>
                        <p style="color: #94a3b8; margin: 0; font-size: 0.85rem;">{download['artist']}</p>
                    </div>
                    <div style="text-align: right;">
                        <span style="color: #22c55e;">✅</span>
                        <p style="color: #64748b; margin: 0; font-size: 0.75rem;">{format_datetime(download['downloaded_at'])}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No downloads yet. Add a playlist to get started!")

    with col2:
        st.subheader("⚠️ Recent Errors")
        recent_errors = db.get_errors(limit=5)
        if recent_errors:
            for error in recent_errors:
                st.markdown(f"""
                <div class="track-item">
                    <div style="flex: 1;">
                        <strong style="color: white;">{error['title'][:40]}</strong>
                        <p style="color: #94a3b8; margin: 0; font-size: 0.85rem;">{error['artist']}</p>
                    </div>
                    <div style="text-align: right;">
                        <span class="status-badge status-error">{error['error_reason'][:20]}</span>
                        <p style="color: #64748b; margin: 0; font-size: 0.75rem;">Attempts: {error['attempts']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("No errors in cache! 🎉")

    # Storage info
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("💾 Storage Overview")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Size", f"{stats['total_size_mb']:.1f} MB")
    with col2:
        st.metric("Unique Artists", stats['unique_artists'])
    with col3:
        st.metric("Download Folder", settings.DOWNLOAD_FOLDER[:30] + "..." if len(settings.DOWNLOAD_FOLDER) > 30 else settings.DOWNLOAD_FOLDER)


elif page == "📋 Playlists":
    st.markdown("""
    <div class="main-header animate-fade-in">
        <h1>📋 Playlist Manager</h1>
        <p>Add and manage your Spotify playlists</p>
    </div>
    """, unsafe_allow_html=True)

    # Add new playlist
    with st.expander("➕ Add New Playlist", expanded=False):
        with st.form("add_playlist_form"):
            playlist_url = st.text_input(
                "Spotify Playlist URL",
                placeholder="https://open.spotify.com/playlist/..."
            )
            playlist_name = st.text_input(
                "Playlist Name",
                placeholder="My Awesome Playlist"
            )

            submitted = st.form_submit_button("Add Playlist", type="primary")

            if submitted and playlist_url:
                try:
                    # Extract playlist ID from URL
                    spotify_id = playlist_url.split("/")[-1].split("?")[0]
                    name = playlist_name or f"Playlist {spotify_id[:8]}"

                    playlist_id = db.add_playlist(
                        spotify_id=spotify_id,
                        name=name,
                        url=playlist_url,
                        track_count=0
                    )

                    st.success(f"✅ Playlist '{name}' added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error adding playlist: {e}")

    # List playlists
    st.subheader("Your Playlists")
    playlists = db.get_playlists()

    if playlists:
        for playlist in playlists:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    st.markdown(f"**{playlist['name']}**")
                    st.caption(f"ID: {playlist['spotify_id'][:15]}...")

                with col2:
                    downloaded = playlist.get('downloaded_count', 0) or 0
                    total = playlist.get('total_tracks', 0) or 0
                    st.metric("Tracks", f"{downloaded}/{total}")

                with col3:
                    errors = playlist.get('error_count', 0) or 0
                    st.metric("Errors", errors)

                with col4:
                    if st.button("🗑️", key=f"del_playlist_{playlist['id']}"):
                        db.delete_playlist(playlist['id'])
                        st.success("Playlist deleted!")
                        st.rerun()

                st.divider()
    else:
        st.info("No playlists yet. Add your first playlist above!")


elif page == "🎵 Tracks":
    st.markdown("""
    <div class="main-header animate-fade-in">
        <h1>🎵 Track Library</h1>
        <p>Browse and manage your music tracks</p>
    </div>
    """, unsafe_allow_html=True)

    # Filters
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_query = st.text_input("🔍 Search tracks", placeholder="Search by title or artist...")

    with col2:
        status_filter = st.selectbox(
            "Status",
            ["All", "Pending", "Downloaded", "Error"]
        )

    with col3:
        playlists = db.get_playlists()
        playlist_options = ["All Playlists"] + [p['name'] for p in playlists]
        playlist_filter = st.selectbox("Playlist", playlist_options)

    # Get tracks
    status_map = {"Pending": "pending", "Downloaded": "downloaded", "Error": "error"}
    selected_status = status_map.get(status_filter)

    playlist_id = None
    if playlist_filter != "All Playlists":
        for p in playlists:
            if p['name'] == playlist_filter:
                playlist_id = p['id']
                break

    if search_query:
        tracks = db.search_tracks(search_query)
    else:
        tracks = db.get_tracks(playlist_id=playlist_id, status=selected_status)

    # Display tracks
    st.subheader(f"📀 {len(tracks)} Tracks")

    if tracks:
        for track in tracks:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    st.markdown(f"**{track['title'][:50]}**")
                    st.caption(f"🎤 {track['artist']} | 📋 {track.get('playlist_name', 'Unknown')}")

                with col2:
                    status_emoji = get_status_emoji(track['status'])
                    st.markdown(f"{status_emoji} {track['status'].title()}")

                with col3:
                    if track['file_path']:
                        st.caption(format_file_size(track.get('file_size')))
                    else:
                        st.caption("—")

                with col4:
                    if st.button("🗑️", key=f"del_track_{track['id']}"):
                        db.delete_track(track['id'])
                        st.success("Track removed!")
                        st.rerun()

                st.divider()
    else:
        st.info("No tracks found matching your filters.")


elif page == "📥 Downloads":
    st.markdown("""
    <div class="main-header animate-fade-in">
        <h1>📥 Download History</h1>
        <p>View your successfully downloaded tracks</p>
    </div>
    """, unsafe_allow_html=True)

    # Search
    search_query = st.text_input("🔍 Search downloads", placeholder="Search by title or artist...")

    # Get downloads
    if search_query:
        downloads = db.search_downloads(search_query)
    else:
        downloads = db.get_downloads(limit=100)

    # Stats bar
    download_stats = db.get_download_stats()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Downloads", download_stats['total_downloads'])
    with col2:
        st.metric("Total Size", f"{download_stats['total_size_mb']:.1f} MB")
    with col3:
        st.metric("Unique Artists", download_stats['unique_artists'])

    st.divider()

    # Downloads list
    if downloads:
        for download in downloads:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"**{download['title']}**")
                    st.caption(f"🎤 {download['artist']} | 💿 {download.get('album', 'Unknown Album')}")

                with col2:
                    st.caption(f"📁 {format_file_size(download.get('file_size'))}")
                    st.caption(f"🎵 {download['quality']}")

                with col3:
                    st.caption(format_datetime(download['downloaded_at']))

                st.divider()
    else:
        st.info("No downloads yet. Start downloading music to see them here!")


elif page == "⚠️ Errors":
    st.markdown("""
    <div class="main-header animate-fade-in">
        <h1>⚠️ Error Cache</h1>
        <p>Manage failed download attempts</p>
    </div>
    """, unsafe_allow_html=True)

    # Error stats
    error_stats = db.get_error_stats()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric("Total Errors", error_stats['total_errors'])

        if st.button("🗑️ Clear All Errors", type="secondary"):
            cleared = db.clear_all_errors()
            st.success(f"Cleared {cleared} errors!")
            st.rerun()

    with col2:
        if error_stats['by_reason']:
            st.subheader("Errors by Reason")
            for reason, count in error_stats['by_reason'].items():
                progress = count / error_stats['total_errors'] if error_stats['total_errors'] > 0 else 0
                st.markdown(f"**{reason}**: {count}")
                st.progress(progress)

    st.divider()

    # Error list
    errors = db.get_errors(limit=50)

    if errors:
        st.subheader(f"📋 {len(errors)} Cached Errors")

        for error in errors:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"**{error['title'][:50]}**")
                    st.caption(f"🎤 {error['artist']}")

                with col2:
                    st.markdown(f"<span class='status-badge status-error'>{error['error_reason']}</span>", unsafe_allow_html=True)
                    st.caption(f"Attempts: {error['attempts']}")

                with col3:
                    st.caption(format_datetime(error['updated_at']))
                    if st.button("🔄 Retry", key=f"retry_error_{error['id']}"):
                        db.clear_error(error['id'])
                        st.success("Error cleared! Track can be retried.")
                        st.rerun()

                st.divider()
    else:
        st.success("🎉 No errors in cache! All tracks processed successfully.")


elif page == "⚙️ Settings":
    st.markdown("""
    <div class="main-header animate-fade-in">
        <h1>⚙️ Settings</h1>
        <p>Configure your Dreamlight experience</p>
    </div>
    """, unsafe_allow_html=True)

    # Current settings
    st.subheader("📁 Current Configuration")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Download Settings**")
        st.text_input("Download Folder", value=settings.DOWNLOAD_FOLDER, disabled=True)
        st.text_input("Data Directory", value=settings.DATA_DIR, disabled=True)
        st.number_input("Download Timeout (seconds)", value=settings.DOWNLOAD_TIMEOUT, disabled=True)
        st.number_input("Max Retries", value=settings.RETRY_MAX_COUNT, disabled=True)

    with col2:
        st.markdown("**Spotify Settings**")
        st.text_input("Client ID", value="*" * 20 if settings.SPOTIFY_CLIENT_ID else "Not set", disabled=True)
        st.text_input("Client Secret", value="*" * 20 if settings.SPOTIFY_CLIENT_SECRET else "Not set", disabled=True)
        st.text_input("Default Playlist URL", value=settings.SPOTIFY_PLAYLIST_URL[:50] + "..." if len(settings.SPOTIFY_PLAYLIST_URL) > 50 else settings.SPOTIFY_PLAYLIST_URL, disabled=True)

    st.divider()

    # Database info
    st.subheader("💾 Database Information")

    db_path = db.db_path
    db_exists = os.path.exists(db_path)
    db_size = os.path.getsize(db_path) if db_exists else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Database Status", "✅ Connected" if db_exists else "❌ Not Found")
    with col2:
        st.metric("Database Size", format_file_size(db_size))
    with col3:
        st.metric("Database Path", db_path.split("/")[-1])

    st.text_input("Full Database Path", value=db_path, disabled=True)

    st.divider()

    # Danger zone
    st.subheader("⚠️ Danger Zone")

    with st.expander("🗑️ Clear All Data"):
        st.warning("This will permanently delete all your data including playlists, tracks, downloads history, and error cache.")

        confirm = st.text_input("Type 'DELETE ALL' to confirm")

        if st.button("🗑️ Delete All Data", type="secondary"):
            if confirm == "DELETE ALL":
                # Clear all tables
                db.clear_all_errors()
                for playlist in db.get_playlists():
                    db.delete_playlist(playlist['id'])
                st.success("All data has been deleted!")
                st.rerun()
            else:
                st.error("Please type 'DELETE ALL' to confirm.")

    st.divider()

    # About
    st.subheader("ℹ️ About Dreamlight")
    st.markdown("""
    **Dreamlight** is a beautiful interface for managing your FLAC music downloads.

    - 🎵 **FLAC Quality**: Download music in lossless FLAC format
    - 📋 **Playlist Support**: Import and manage Spotify playlists
    - 💾 **SQLite Database**: Efficient local storage
    - 🎨 **Modern UI**: Beautiful, responsive Streamlit interface

    Built with ❤️ using Streamlit and Python.
    """)


# Footer
st.markdown("""
<div style="text-align: center; padding: 2rem; margin-top: 2rem; border-top: 1px solid rgba(99, 102, 241, 0.2);">
    <p style="color: #64748b; font-size: 0.85rem;">
        🎵 Dreamlight - FLAC Downloader Manager | Built with Streamlit
    </p>
</div>
""", unsafe_allow_html=True)
