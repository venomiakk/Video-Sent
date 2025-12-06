import subprocess
import sys
import os

# --- KONFIGURACJA ---
COLLECTION_FILE = "tests/api/api_tests.postman_collection.json"
REPORT_FILE = "tests/api/api_report.html"

# Kolory
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
YELLOW = "\033[93m"

def check_requirements():
    """Sprawdza czy plik kolekcji istnieje."""
    if not os.path.exists(COLLECTION_FILE):
        print(f"{RED}BŁĄD: Nie znaleziono pliku {COLLECTION_FILE}{RESET}")
        print("Upewnij się, że zapisałeś JSON z Postmana w tym katalogu.")
        sys.exit(1)

def run_tests():
    """Uruchamia Newmana przez subprocess."""
    print(f"{YELLOW}>>> Uruchamianie testów Newman...{RESET}")
    
    # Komenda, którą wpisałbyś w terminalu:
    # newman run plik.json -r cli,html --reporter-html-export raport.html
    command = [
        "newman", 
        "run", 
        COLLECTION_FILE, 
        "--reporters", "cli,html", 
        "--reporter-html-export", REPORT_FILE
    ]

    try:
        # shell=True na Windows może być wymagane, na Mac/Linux zazwyczaj False jest bezpieczniejsze
        # check=True rzuci wyjątek, jeśli testy nie przejdą (exit code != 0)
        subprocess.run(command, check=True)
        
        print(f"\n{GREEN}✅ Wszystkie testy przeszły pomyślnie!{RESET}")
        print(f"Raport HTML wygenerowano w: {os.path.abspath(REPORT_FILE)}")
        
    except subprocess.CalledProcessError:
        print(f"\n{RED}❌ Niektóre testy nie przeszły.{RESET}")
        print(f"Sprawdź raport: {os.path.abspath(REPORT_FILE)}")
        sys.exit(1)
        
    except FileNotFoundError:
        print(f"\n{RED}❌ BŁĄD: Nie znaleziono polecenia 'newman'.{RESET}")
        print("Czy zainstalowałeś Node.js i Newmana?")
        print("Komenda: npm install -g newman newman-reporter-html")
        sys.exit(1)

if __name__ == "__main__":
    check_requirements()
    run_tests()