import os
import time
import random
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# --- USTAWIENIA ---
INPUT_URL = "https://www.amazon.pl/product-reviews/B0BHJJ36HS/ref=cm_cr_arp_d_show_all?ie=UTF8&reviewerType=all_reviews"
BRAND = "motorola"
MODEL = "g72"
LIMIT = 100

# --- START FIREFOXA ---
options = webdriver.FirefoxOptions()
print("Uruchamiam Firefoxa...")
driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)

if not os.path.exists("Opinie/PL"): os.makedirs("Opinie/PL", exist_ok=True)
if not os.path.exists("Opinie/EN"): os.makedirs("Opinie/EN", exist_ok=True)

stats = {"PL_P": 0, "PL_N": 0, "EN_P": 0, "EN_N": 0}

def scrape_auto_translate():
    # ZMIANA: source='auto' pozwala wykryć niemiecki/hiszpański i przetłumaczyć
    translator_to_pl = GoogleTranslator(source='auto', target='pl')
    translator_to_en = GoogleTranslator(source='auto', target='en')
    
    print(f"Otwieram stronę startową...")
    driver.get(INPUT_URL)
    
    print("\n" + "="*50)
    print("INSTRUKCJA:")
    print("1. Skrypt pobierze opinie z obecnej strony.")
    print("2. Potem poprosi Cię o zmianę strony (kliknięcie 'Następna' w Firefoxie).")
    print("3. TŁUMACZENIE DZIAŁA W LOCIE (Niemiecki -> PL i EN).")
    print("="*50 + "\n")

    input("Upewnij się, że widać listę opinii i wciśnij ENTER...")

    while True:
        reviews_count = len(os.listdir("Opinie/PL"))
        if reviews_count >= LIMIT:
            print("Mamy 100 plików! Koniec.")
            break

        print(f"\n-> Analizuję stronę (Stan: {reviews_count}/{LIMIT})...")
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        reviews = soup.find_all('div', {'data-hook': 'review'})
        if not reviews: reviews = soup.select('div[id^="customer_review"]')
        
        if not reviews:
            print("!!! Nie widzę opinii. Przewiń stronę lub rozwiąż Captchę i wciśnij ENTER...")
            input()
            continue

        for review in reviews:
            if reviews_count >= LIMIT: break
            
            try:
                # 1. Pobranie ORYGINAŁU (np. po niemiecku)
                body = review.find('span', {'data-hook': 'review-body'})
                if not body: continue
                raw_content = body.get_text().strip()
                if not raw_content: continue

                # Ocena
                try:
                    score_text = review.find('i', {'data-hook': 'review-star-rating'}).get_text()
                    score_val = float(score_text.split(',')[0])
                except:
                    try:
                        score_text = review.find('i', class_='a-icon-star').get_text()
                        score_val = float(score_text.split(',')[0])
                    except: score_val = 5.0

                score_normalized = score_val / 5.0
                sentiment = "P" if score_val >= 3.5 else "N"
                
                # ID
                review_id = review.get('id', str(random.randint(10000,99999)))
                if any(review_id in f for f in os.listdir("Opinie/PL")): continue

                filename = f"{BRAND}_{MODEL}_{score_normalized:.3f}_{sentiment}_{review_id}.txt"

                # 2. Tłumaczenie na POLSKI (do folderu PL)
                # Żebyś w folderze PL miał polski tekst, a nie niemiecki
                try:
                    content_pl = translator_to_pl.translate(raw_content)
                except:
                    content_pl = raw_content # Jak błąd, zostaw oryginał

                with open(f"Opinie/PL/{filename}", "w", encoding="utf-8") as f:
                    f.write(content_pl)
                
                if sentiment == "P": stats["PL_P"] += 1
                else: stats["PL_N"] += 1

                # 3. Tłumaczenie na ANGIELSKI (do folderu EN)
                try:
                    content_en = translator_to_en.translate(raw_content)
                    with open(f"Opinie/EN/{filename}", "w", encoding="utf-8") as f:
                        f.write(content_en)
                    
                    if sentiment == "P": stats["EN_P"] += 1
                    else: stats["EN_N"] += 1
                except: pass

                reviews_count += 1
                print(f"Pobrano i przetłumaczono: {filename}")

            except Exception as e:
                continue
        
        if reviews_count < LIMIT:
            print("\n>>> ZADANIE DLA CIEBIE <<<")
            print("Kliknij 'Następna strona' w Firefoxie.")
            input("Jak się załaduje, wciśnij ENTER tutaj...")
        else:
            break

    driver.quit()
    print("\nGOTOWE! Koniec pracy.")
    print(f"Pozytywne: {stats['PL_P']}, Negatywne: {stats['PL_N']}")

if __name__ == "__main__":
    scrape_auto_translate()