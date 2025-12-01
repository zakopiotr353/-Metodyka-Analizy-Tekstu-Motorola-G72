import os
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from deep_translator import GoogleTranslator

# --- USTAWIENIA ---
# ID produktu: Motorola G72 (wersja czarna, dużo opinii)
PRODUCT_ID = "141022311"
LIMIT = 100
BRAND = "motorola"
MODEL = "g72"

# --- KONFIGURACJA FIREFOXA ---
options = webdriver.FirefoxOptions()
# options.add_argument("--headless") # Odkomentuj, żeby ukryć okno
options.set_preference("dom.webdriver.enabled", False)
options.set_preference('useAutomationExtension', False)

print("Uruchamiam przeglądarkę Firefox...")
# Pobieranie i instalacja sterownika do Firefoxa (GeckoDriver)
driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)

# --- FOLDERY ---
if not os.path.exists("Opinie"): os.mkdir("Opinie")
if not os.path.exists("Opinie/PL"): os.mkdir("Opinie/PL")
if not os.path.exists("Opinie/EN"): os.mkdir("Opinie/EN")

stats = {"PL_P": 0, "PL_N": 0, "EN_P": 0, "EN_N": 0}

def scrape_firefox():
    translator = GoogleTranslator(source='pl', target='en')
    
    # Sprawdzamy ile plików już mamy
    existing_files = len([name for name in os.listdir("Opinie/PL") if os.path.isfile(os.path.join("Opinie/PL", name))])
    reviews_count = existing_files
    print(f"Znaleziono {reviews_count} już pobranych opinii. Kontynuuję...")

    # Wyliczamy stronę startową
    page = (reviews_count // 10) + 1
    
    print(f"--- START: Pobieranie opinii dla {BRAND} {MODEL} ---")

    while reviews_count < LIMIT:
        url = f"https://www.ceneo.pl/{PRODUCT_ID}/opinie-{page}"
        print(f"-> Wchodzę na stronę {page}...")
        
        try:
            driver.get(url)
            time.sleep(random.uniform(3, 6)) # Czekamy aż strona się załaduje

            # Sprawdzenie CAPTCHA
            if "captcha" in driver.page_source.lower():
                print("\n!!! WYKRYTO CAPTCHA !!!")
                print("Rozwiąż obrazki w otwartym oknie Firefoxa.")
                print("Jak skończysz i zobaczysz opinie - wciśnij ENTER tutaj w konsoli.")
                input("Czekam na Enter...")
            
            # Szukanie opinii
            reviews = driver.find_elements(By.CLASS_NAME, "js_product-review")
            
            if not reviews:
                print("Brak (więcej) opinii na tej stronie. Koniec.")
                break

            for review in reviews:
                if reviews_count >= LIMIT:
                    break

                try:
                    review_id = review.get_attribute("data-entry-id")
                    if not review_id: continue

                    # Sprawdź czy już mamy ten plik (żeby nie dublować)
                    already_exists = False
                    for existing in os.listdir("Opinie/PL"):
                        if review_id in existing:
                            already_exists = True
                            break
                    
                    if already_exists:
                        continue 

                    # Ocena
                    score_elem = review.find_element(By.CLASS_NAME, "user-post__score-count")
                    score_text = score_elem.text.split('/')[0].replace(',', '.')
                    score_val = float(score_text)
                    score_normalized = score_val / 5.0
                    
                    # Treść
                    text_elem = review.find_element(By.CLASS_NAME, "user-post__text")
                    content_pl = text_elem.text.strip()
                    
                    # Sentyment
                    sentiment = "P" if score_val >= 3.5 else "N"
                    
                    # Nazwa pliku
                    filename = f"{BRAND}_{MODEL}_{score_normalized:.3f}_{sentiment}_{review_id}.txt"
                    
                    # Zapis PL
                    with open(f"Opinie/PL/{filename}", "w", encoding="utf-8") as f:
                        f.write(content_pl)
                    
                    if sentiment == "P": stats["PL_P"] += 1
                    else: stats["PL_N"] += 1

                    # Tłumaczenie i Zapis EN
                    try:
                        content_en = translator.translate(content_pl)
                        with open(f"Opinie/EN/{filename}", "w", encoding="utf-8") as f:
                            f.write(content_en)
                        
                        if sentiment == "P": stats["EN_P"] += 1
                        else: stats["EN_N"] += 1
                    except:
                        pass
                    
                    reviews_count += 1
                    print(f"Pobrano {reviews_count}/{LIMIT}: {filename}")

                except Exception:
                    continue 

            page += 1

        except Exception as e:
            print(f"Błąd strony: {e}")
            break

    driver.quit()

    # Zliczamy finalnie pliki w folderze dla pewności
    pl_files = os.listdir("Opinie/PL")
    pos_cnt = sum(1 for f in pl_files if "_P_" in f)
    neg_cnt = sum(1 for f in pl_files if "_N_" in f)

    print("\n" + "="*40)
    print("GOTOWE! DANE DO WPISANIA W TABELKĘ:")
    print("="*40)
    print(f"Marka: {BRAND}")
    print(f"Model: {MODEL}")
    print(f"Opinie pozytywne PL: {pos_cnt}")
    print(f"Opinie negatywne PL: {neg_cnt}")
    print(f"Opinie pozytywne EN: {pos_cnt}")
    print(f"Opinie negatywne EN: {neg_cnt}")
    print("="*40)

if __name__ == "__main__":
    scrape_firefox()