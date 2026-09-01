from datetime import datetime
import os
from github import Github
from google import genai
from PIL import Image
import streamlit as st

st.set_page_config(
    page_title="Zabawna Galeria dla Par 💖", page_icon="📸", layout="centered"
)

st.title("Nasza Szalona Galeria Par 🤪💖")
st.write(
    "Wrzućcie zdjęcie, a darmowe AI od Google dopisze do niego przezabawny"
    " komentarz!"
)

# --- Konfiguracja Kluczy (GitHub + Google Gemini) ---
try:
  GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
  REPO_NAME = st.secrets["REPO_NAME"]
  GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
  st.error(
      "Brak skonfigurowanych sekretów w Streamlit (GitHub / GEMINI_API_KEY)!"
  )
  st.stop()

# Inicjalizacja klientów
g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)
client = genai.Client(api_key=GEMINI_API_KEY)

# --- Wybór stylu przeróbki ---
st.subheader("1. Wybierz szaloną sytuację 🎭")
style_choice = st.selectbox(
    "Kim dzisiaj jesteś na zdjęciu?",
    [
        "Zagubiony poszukiwacz przygód na safari z małpką",
        "Groźny pirat szukający ukrytego skarbu w salonie",
        "Kosmonauta, który ląduje na kanapie",
        "Średniowieczny rycerz walczący z pilotem od telewizora",
    ],
)

# --- Przesyłanie zdjęcia ---
st.subheader("2. Wgraj zdjęcie")
uploaded_file = st.file_uploader(
    "Wybierz zdjęcie twarzy", type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
  original_image = Image.open(uploaded_file)
  st.image(original_image, caption="Twoje zdjęcie", width=300)

  if st.button("Generuj żart i zapisz w galerii! 🚀"):
    with st.spinner("AI myśli nad złośliwym i śmiesznym żartem... ⏳"):
      try:
        # Generowanie żartu przez darmowy model Gemini
        prompt_text = (
            f"Napisz krótki, bardzo żartobliwy i zgryźliwy komentarz"
            f" w języku polskim (styl memów dla par) do sytuacji, w której"
            f" ta osoba robi minę jak na zdjęciu i bierze udział w scenariuszu:"
            f" {style_choice}. Maksymalnie 2 zdania."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_text,
        )
        funny_comment = response.text.strip()

        # Zapis oryginału zdjęcia oraz pliku tekstowego z komentarzem na GitHubie
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name_img = f"photos/{timestamp}_img.jpg"
        file_name_txt = f"photos/{timestamp}_comment.txt"

        # Zapisujemy zdjęcie tymczasowo
        temp_path = "temp.jpg"
        original_image.save(temp_path)
        with open(temp_path, "rb") as f:
          img_content = f.read()

        # Wysyłka do repozytorium GitHub
        repo.create_file(
            path=file_name_img,
            message=f"Photo {timestamp}",
            content=img_content,
            branch="main",
        )

        repo.create_file(
            path=file_name_txt,
            message=f"Comment {timestamp}",
            content=funny_comment,
            branch="main",
        )

        os.remove(temp_path)
        st.success("Super! Zdjęcie i żart zostały dodane do wspólnej galerii! 🎉")
        st.rerun()

      except Exception as e:
        st.error(f"Wystąpił błąd podczas działania AI: {e}")

st.divider()

# --- Sekcja: Galeria Wspomnień ---
st.subheader("🖼️ Wasza Wspólna Galeria")


@st.cache_data(ttl=15)
def load_gallery():
  try:
    contents = repo.get_contents("photos")
    images = [f for f in contents if f.name.endswith("_img.jpg")]
    images = sorted(images, key=lambda x: x.name, reverse=True)

    gallery = []
    for img in images:
      base_name = img.name.replace("_img.jpg", "")
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


gallery_items = load_gallery()

if not gallery_items:
  st.info("Brak zdjęć w galerii. Dodajcie pierwsze wspomnienie wyżej! 💕")
else:
  for item in gallery_items:
    # Stylizacja dymku czatu z żartem nad zdjęciem
    st.markdown(f"💬 **Komentarz AI:** *{item['comment']}*")
    st.image(item["img_url"], use_container_width=True)
    st.write("---")
