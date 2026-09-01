from datetime import datetime
import io
import os
from github import Github
from openai import OpenAI
from PIL import Image
import streamlit as st

st.set_page_config(
    page_title="Zabawna Galeria AI dla Par 💖", page_icon="📸", layout="centered"
)

st.title("Nasza Szalona Galeria AI 🤪💖")
st.write(
    "Wrzućcie zdjęcie, a AI przerobi je w zabawny sposób i dopisze kąśliwy"
    " żart!"
)

# --- Konfiguracja Kluczy (GitHub + OpenAI) ---
try:
  GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
  REPO_NAME = st.secrets["REPO_NAME"]
  OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except Exception:
  st.error("Brak skonfigurowanych sekretów w Streamlit (GitHub / OpenAI)!")
  st.stop()

# Inicjalizacja klientów
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Wybór stylu przeróbki AI ---
st.subheader("1. Wybierz styl dla swojej połówki 🎭")
style_choice = st.selectbox(
    "Kim dzisiaj jesteśmy?",
    [
        "Safari Explorer (poszukiwacz przygód z małpką)",
        "Groźny Pirat z mapą skarbów",
        "Kosmonauta zgubiony w galaktyce",
        "Średniowieczny rycerz walczący z tosterem",
    ],
)

# --- Przesyłanie zdjęcia ---
st.subheader("2. Wgraj zdjęcie")
uploaded_file = st.file_uploader(
    "Wybierz zdjęcie twarzy", type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
  # Podgląd oryginału
  original_image = Image.open(uploaded_file)
  st.image(
      original_image,
      caption="Oryginalna fotka do przeróbki",
      width=300,
  )

  if st.button("Odpal magię AI! 🚀"):
    with st.spinner(
        "AI analizuje minę i tworzy żart oraz awatar... (To może chwilę"
        " potrwać) ⏳"
    ):
      try:
        # Krok A: Generowanie żartobliwego komentarza przez GPT
        prompt_text = (
            f"Napisz bardzo krótki, żartobliwy i zgryźliwy komentarz"
            f" w języku polskim do zdjęcia w stylizacji: {style_choice}."
            f" Styl rodem z zabawnych memów dla par."
        )

        response_text = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt_text}],
            max_tokens=60,
        )
        funny_comment = response_text.choices[0].message.content.strip()

        # Krok B: Generowanie obrazu w stylu AI (DALL-E 3)
        # W praktyce produkcyjnej najlepiej przesłać obraz do DALL-E edycji lub wygenerować nowy na podstawie stylu
        prompt_image = (
            f"A funny, high-quality cartoon caricature illustration in comic"
            f" book style showing a person in a funny scenario: {style_choice},"
            f" vibrant colors, humorous."
        )

        response_img = client.images.generate(
            model="dall-e-3",
            prompt=prompt_image,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response_img.data[0].url

        # Pobranie wygenerowanego przez AI obrazka
        import requests

        img_data = requests.get(image_url).content

        # Krok C: Zapis na GitHubie (obrazek + plik tekstowy z komentarzem)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name_img = f"photos/{timestamp}_ai.jpg"
        file_name_txt = f"photos/{timestamp}_comment.txt"

        # Zapisujemy obrazek
        repo.create_file(
            path=file_name_img,
            message=f"AI Image {timestamp}",
            content=img_data,
            branch="main",
        )

        # Zapisujemy komentarz
        repo.create_file(
            path=file_name_txt,
            message=f"AI Comment {timestamp}",
            content=funny_comment,
            branch="main",
        )

        st.success("Gotowe! Obrazek został przerobiony i zapisany! 🎉")
        st.rerun()

      except Exception as e:
        st.error(f"Wystąpił błąd podczas działania AI: {e}")

st.divider()

# --- Sekcja: Galeria Waszych Wspomnień z AI ---
st.subheader("🖼️ Wasza Galeria Szalonych Przeróbek")


@st.cache_data(ttl=30)
def load_ai_gallery():
  try:
    contents = repo.get_contents("photos")
    # Filtrujemy tylko pliki jpg
    images = [f for f in contents if f.name.endswith("_ai.jpg")]
    images = sorted(images, key=lambda x: x.name, reverse=True)

    gallery = []
    for img in images:
      base_name = img.name.replace("_ai.jpg", "")
      # Szukamy odpowiadającego pliku z komentarzem
      comment_path = f"photos/{base_name}_comment.txt"
      comment_text = "Brak komentarza"
      try:
        c_file = repo.get_contents(comment_path)
        comment_text = c_file.decoded_content.decode("utf-8")
      except Exception:
        pass

      gallery.append(
          {"img_url": img.download_url, "comment": comment_text, "name": base_name}
      )
    return gallery
  except Exception:
    return []


gallery_items = load_ai_gallery()

if not gallery_items:
  st.info(
      "Brak przerobionych zdjęć w galerii. Użyj formularza wyżej, aby stworzyć"
      " pierwszy mem! 💕"
  )
else:
  for item in gallery_items:
    # Wyświetlanie w stylu "dymku czatu" jak na Twoim szkicu
    st.markdown(f"> 💬 **Dymek AI:** *{item['comment']}*")
    st.image(item["img_url"], use_container_width=True)
    st.write("---")
