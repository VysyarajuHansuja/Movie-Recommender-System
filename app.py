import streamlit as st
import pickle
import pandas as pd
import requests

# --- HELPER FUNCTION TO LOAD CSS ---
def local_css(file_name):
    """Loads a local CSS file for styling."""
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"'{file_name}' not found. Please make sure the CSS file is in the same directory.")

# --- PAGE CONFIGURATION (must be the first Streamlit command) ---
st.set_page_config(
    page_title="Cinematch",
    page_icon="🎬",
    layout="wide",
)

# --- LOAD LOCAL CSS ---
local_css("style.css")

# --- API AND RECOMMENDATION FUNCTIONS ---
def fetch_poster(movie_id):
    """Fetches the movie poster URL from the TMDB API."""
    try:
        # Securely access the API key from secrets.toml
        api_key = st.secrets['tmdb_api_key']
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
        
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        
        poster_path = data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path
        else:
            # Return a placeholder image if no poster is found
            return "https://via.placeholder.com/500x750.png?text=No+Poster"
            
    except (requests.exceptions.RequestException, KeyError):
        # Handle API errors or missing keys gracefully
        return "https://via.placeholder.com/500x750.png?text=API+Error"

def recommend(movie):
    """Recommends 5 similar movies."""
    try:
        movie_index = movies[movies['title'] == movie].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]
        
        recommended_names = []
        recommended_posters = []
        for i in movies_list:
            movie_id = movies.iloc[i[0]].movie_id
            recommended_names.append(movies.iloc[i[0]].title)
            recommended_posters.append(fetch_poster(movie_id))
        return recommended_names, recommended_posters
    except IndexError:
        return [], []

# --- LOAD DATA ---
try:
    # Load the pre-processed movie data and similarity matrix
    movie_list = pickle.load(open('movie_list.pkl', 'rb'))
    similarity = pickle.load(open('similarity.pkl', 'rb'))
    movies = pd.DataFrame(movie_list)
except FileNotFoundError:
    st.error("Data files not found. Please ensure 'movie_list.pkl' and 'similarity.pkl' are in the directory.")
    st.stop() # Stop the app if data files are missing

# --- STREAMLIT UI ---
st.title("🎬 Cinematch Movie Recommender")
st.markdown("### Find your next favorite movie!")

# Movie selection dropdown
selected_movie_name = st.selectbox(
    'Type or select a movie you like:',
    movies['title'].values
)

# Recommendation button
if st.button('Recommend'):
    with st.spinner('Finding similar movies...'):
        names, posters = recommend(selected_movie_name)
    
        if names:
            st.subheader("Here are some movies you might like:")
            # Create 5 columns for the recommendations
            cols = st.columns(5, gap="medium")
            for i in range(len(names)):
                with cols[i]:
                    st.image(posters[i])
                    st.markdown(f"**{names[i]}**")
        else:
            st.warning("Could not find recommendations for the selected movie.")
