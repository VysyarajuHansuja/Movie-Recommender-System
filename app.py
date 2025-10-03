import streamlit as st
import pickle
import pandas as pd
import requests
import os
import gdown

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Cinematch",
    page_icon="🎬",
    layout="wide",
)

# --- HELPER FUNCTIONS ---
def local_css(file_name):
    """Loads a local CSS file for styling."""
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

import gdown
import os
import streamlit as st
import pickle

def download_file_from_gdrive(file_id, destination):
    """Download a file from Google Drive and verify it's not HTML."""
    url = f"https://drive.google.com/uc?id={file_id}"

    try:
        with st.spinner(f"Downloading {destination}..."):
            gdown.download(url, destination, quiet=False, fuzzy=True)
    except Exception as e:
        st.error(f"Download failed for {destination}. Error: {e}")
        st.stop()

    # Verify it's really a pickle, not HTML
    try:
        with open(destination, "rb") as f:
            first_bytes = f.read(4)
        if first_bytes.startswith(b"<"):
            raise ValueError("Downloaded file looks like HTML, not a pickle.")
    except Exception as e:
        st.error(f"File validation failed for {destination}: {e}")
        st.stop()


def fetch_poster(movie_id):
    """Fetches the movie poster URL from the TMDB API."""
    
    api_key = st.secrets['tmdb_api_key']
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path
        else:
            return "https://via.placeholder.com/500x750.png?text=No+Poster"
    
    except (requests.exceptions.RequestException, KeyError):
        return "https://via.placeholder.com/500x750.png?text=API+Error"

def recommend(movie_title, movies_df, similarity_matrix):
    """Recommends 5 similar movies."""
    try:
        movie_index = movies_df[movies_df['title'] == movie_title].index[0]
        distances = similarity_matrix[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
        
        names, posters = [], []
        for i in movies_list:
            movie_id = movies_df.iloc[i[0]].movie_id
            names.append(movies_df.iloc[i[0]].title)
            posters.append(fetch_poster(movie_id))
        return names, posters
    except IndexError:
        return [], []

# --- LOAD LOCAL CSS ---
local_css("style.css")

# --- DATA LOADING AND DOWNLOADING ---
MOVIE_LIST_PATH = 'movie_list.pkl'
SIMILARITY_PATH = 'similarity.pkl'
MOVIE_LIST_GDRIVE_ID = "1hUq9eOgjlgzgSK1jiY_Sq66qwuqGfadI" 
SIMILARITY_GDRIVE_ID = "1kX8VdZlvWFN9pG343S2bsFMTfHER25NP"

if not os.path.exists(MOVIE_LIST_PATH):
    download_file_from_gdrive(MOVIE_LIST_GDRIVE_ID, MOVIE_LIST_PATH)
if not os.path.exists(SIMILARITY_PATH):
    download_file_from_gdrive(SIMILARITY_GDRIVE_ID, SIMILARITY_PATH)

# Load the data files with improved error handling
try:
    with open(MOVIE_LIST_PATH, 'rb') as f1:
        movie_list = pickle.load(f1)
    movies = pd.DataFrame(movie_list)
except (pickle.UnpicklingError, FileNotFoundError) as e:
    st.error(f"Failed to load '{MOVIE_LIST_PATH}': {e}. Please ensure the Google Drive ID is correct and the file is shared as 'Anyone with the link'.")
    st.stop()

try:
    with open(SIMILARITY_PATH, 'rb') as f2:
        similarity = pickle.load(f2)
except (pickle.UnpicklingError, FileNotFoundError) as e:
    st.error(f"Failed to load '{SIMILARITY_PATH}': {e}. Please ensure the Google Drive ID is correct and the file is shared as 'Anyone with the link'.")
    st.stop()


# --- STREAMLIT UI ---
st.title("🎬 Cinematch Movie Recommender")
st.markdown("### Find your next favorite movie!")

selected_movie_name = st.selectbox(
    'Type or select a movie you like:',
    movies['title'].values
)

if st.button('Recommend'):
    with st.spinner('Finding similar movies...'):
        names, posters = recommend(selected_movie_name, movies, similarity)
    
        if names:
            st.subheader("Here are some movies you might like:")
            cols = st.columns(5, gap="medium")
            for i in range(len(names)):
                with cols[i]:
                    st.image(posters[i])
                    st.markdown(f"**{names[i]}**")
        else:
            st.warning("Could not find recommendations for the selected movie.")

