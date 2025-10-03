import streamlit as st
import pickle
import pandas as pd
import requests
import os

# --- PAGE CONFIGURATION (must be the first Streamlit command) ---
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
        st.error(f"'{file_name}' not found. Please ensure the CSS file is in the same directory.")

def download_file_from_gdrive(file_id, destination):
    """Downloads a file from a public Google Drive link."""
    URL = f"https://docs.google.com/uc?export=download&id={file_id}"
    
    with st.spinner(f"Downloading required model file: {destination}... (this may take a minute)"):
        response = requests.get(URL, stream=True)
        response.raise_for_status()
        
        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    st.success(f"Downloaded {destination} successfully!")

def fetch_poster(movie_id):
    """Fetches the movie poster URL from the TMDB API."""
    try:
        api_key = st.secrets['tmdb_api_key']
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
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
# Define file paths and Google Drive IDs
MOVIE_LIST_PATH = 'movie_list.pkl'
SIMILARITY_PATH = 'similarity.pkl'

# ❗️ PASTE YOUR GOOGLE DRIVE FILE IDs HERE
MOVIE_LIST_GDRIVE_ID = '1hUq9eOgjlgzgSK1jiY_Sq66qwuqGfadI' 
SIMILARITY_GDRIVE_ID = '1p0OeGB63QVtjA51VFbvDMT-2eahmB_gl'

# Check for movie_list.pkl and download if it doesn't exist
if not os.path.exists(MOVIE_LIST_PATH):
    download_file_from_gdrive(MOVIE_LIST_GDRIVE_ID, MOVIE_LIST_PATH)

# Check for similarity.pkl and download if it doesn't exist
if not os.path.exists(SIMILARITY_PATH):
    download_file_from_gdrive(SIMILARITY_GDRIVE_ID, SIMILARITY_PATH)

# Load the data files
try:
    movie_list = pickle.load(open(MOVIE_LIST_PATH, 'rb'))
    similarity = pickle.load(open(SIMILARITY_PATH, 'rb'))
    movies = pd.DataFrame(movie_list)
except FileNotFoundError:
    st.error("Model files not found. Please ensure the Google Drive IDs are correct and the files are accessible.")
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




