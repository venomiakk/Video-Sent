import re
from playwright.sync_api import Page, expect

FRONTEND_URL = "http://localhost:3000"
API_URL = "http://localhost:8000/api/v1/auth"

def test_login_ui_layout(page: Page):
    """Sprawdza czy strona logowania wygląda poprawnie."""
    page.goto(f"{FRONTEND_URL}/login")

    expect(page.get_by_role("heading", name="Witaj ponownie")).to_be_visible()
    
    expect(page.get_by_label("Adres email")).to_be_visible()
    expect(page.get_by_label("Hasło")).to_be_visible()
    
    expect(page.get_by_role("button", name="Kontynuuj")).to_be_visible()

    page.get_by_role("button", name="Zarejestruj się").click()
    
    expect(page.get_by_role("heading", name="Utwórz konto")).to_be_visible()

def test_login_success(page: Page):
    """POZYTYWNY: Poprawne logowanie (z mockiem API)."""
    
    page.route(f"{API_URL}/login", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"access_token": "fake_token_123", "user": {"email": "test@user.com", "id": "1"}}'
    ))

    page.goto(f"{FRONTEND_URL}/login")
   
    page.get_by_label("Adres email").fill("test@user.com")
    page.get_by_label("Hasło").fill("password123")
    
    page.get_by_role("button", name="Kontynuuj").click()
    
    expect(page).to_have_url(f"{FRONTEND_URL}/")
    
    expect(page.locator(".user-email")).to_contain_text("test@user.com")

def test_login_failure_invalid_credentials(page: Page):
    """NEGATYWNY: Błąd logowania (złe hasło)."""
   
    page.route(f"{API_URL}/login", lambda route: route.fulfill(
        status=401,
        content_type="application/json",
        body='{"detail": "Nieprawidłowy email lub hasło"}'
    ))

    page.goto(f"{FRONTEND_URL}/login")
    
    page.get_by_label("Adres email").fill("wrong@user.com")
    page.get_by_label("Hasło").fill("wrongpass")
  
    page.get_by_role("button", name="Kontynuuj").click()

    error_msg = page.locator(".error-message")
    expect(error_msg).to_be_visible()
 
    expect(error_msg).to_contain_text("Nieprawidłowy email lub hasło")

def test_register_success(page: Page):
    """POZYTYWNY: Rejestracja nowego użytkownika."""

    page.route(f"{API_URL}/register", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"access_token": "new_token_123", "user": {"email": "new@user.com", "id": "2"}}'
    ))

    page.goto(f"{FRONTEND_URL}/login")

    page.get_by_role("button", name="Zarejestruj się").click()
    
    expect(page.get_by_role("heading", name="Utwórz konto")).to_be_visible()

    page.get_by_label("Adres email").fill("new@user.com")
    page.get_by_label("Hasło").fill("strongpass")
    
    page.locator('button[type="submit"]').click()

    expect(page).to_have_url(f"{FRONTEND_URL}/")

def test_auth_validation_html5(page: Page):
    """NEGATYWNY: Walidacja HTML5 (puste pola)."""
    page.goto(f"{FRONTEND_URL}/login")
    

    email_input = page.get_by_label("Adres email")
    submit_btn = page.get_by_role("button", name="Kontynuuj")
    
    submit_btn.click()
    

    is_valid = email_input.evaluate("el => el.checkValidity()")
    assert is_valid is False

def test_logout(page: Page):
    """Funkcjonalność wylogowania."""

    page.goto(FRONTEND_URL)
    page.evaluate("""() => {
        localStorage.setItem('access_token', 'fake_token');
        localStorage.setItem('user', JSON.stringify({email: 'logout@test.com'}));
    }""")
    
    page.goto(FRONTEND_URL)
    expect(page.locator(".user-email")).to_contain_text("logout@test.com")
    
    page.get_by_role("button", name="Wyloguj się").click()
    
    expect(page).to_have_url(re.compile(".*/login"))
    token = page.evaluate("localStorage.getItem('access_token')")
    assert token is None