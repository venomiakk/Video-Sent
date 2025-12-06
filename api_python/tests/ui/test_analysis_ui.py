import re
from playwright.sync_api import Page, expect

FRONTEND_URL = "http://localhost:3000"

def test_dashboard_structure(page: Page):
    """Sprawdza wygląd Dashboardu po zalogowaniu."""
    page.goto(FRONTEND_URL)
    page.evaluate("""() => {
        localStorage.setItem('access_token', 'valid_token_structure');
        localStorage.setItem('user', JSON.stringify({email: 'ui@test.com'}));
    }""")
    page.goto(FRONTEND_URL)

    expect(page.locator(".sidebar")).to_be_visible()
    expect(page.get_by_text("Analizy NLP")).to_be_visible()
    expect(page.locator(".new-analysis-btn")).to_be_visible()
    
    expect(page.get_by_text("Analiza NLP Filmików")).to_be_visible()
    expect(page.locator(".url-input")).to_be_visible()

def test_analysis_validation_empty_url(page: Page):
    """NEGATYWNY: Próba wysłania pustego linku."""
    page.goto(FRONTEND_URL)
    page.evaluate("""() => {
        localStorage.setItem('access_token', 'token');
        localStorage.setItem('user', JSON.stringify({email: 'test@test.com'}));
    }""")
    page.goto(FRONTEND_URL)

    dialog_appeared = False
    
    def handle_dialog(dialog):
        nonlocal dialog_appeared
        dialog_appeared = True
        assert dialog.message == "Proszę podać URL filmu"
        dialog.accept()

    page.on("dialog", handle_dialog)
    
    analyze_btn = page.locator("button.analyze-btn")
    expect(analyze_btn).to_be_disabled()


def test_analysis_input_interaction(page: Page):
    """Interakcja z formularzem analizy."""
    page.goto(FRONTEND_URL)
    page.evaluate("""() => {
        localStorage.setItem('access_token', 'token');
        localStorage.setItem('user', JSON.stringify({email: 'test@test.com'}));
    }""")
    page.goto(FRONTEND_URL)

    input_field = page.locator(".url-input")
    analyze_btn = page.locator("button.analyze-btn")

    expect(analyze_btn).to_be_disabled()

    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    input_field.fill(test_url)
    
    expect(input_field).to_have_value(test_url)
    
    expect(analyze_btn).not_to_be_disabled()

def test_sidebar_navigation(page: Page):
    """Sprawdza czy lista analiz (pusta) renderuje się poprawnie."""
    page.goto(FRONTEND_URL)
    page.evaluate("""() => {
        localStorage.setItem('access_token', 'token');
        localStorage.setItem('user', JSON.stringify({email: 'test@test.com'}));
    }""")
    page.goto(FRONTEND_URL)

    if page.locator(".empty-state").is_visible():
        expect(page.get_by_text("Brak analiz")).to_be_visible()

def test_create_new_analysis_button(page: Page):
    """Sprawdza działanie przycisku '+ Nowa analiza'."""
    page.goto(FRONTEND_URL)
    page.evaluate("""() => {
        localStorage.setItem('access_token', 'token');
        localStorage.setItem('user', JSON.stringify({email: 'test@test.com'}));
    }""")
    page.goto(FRONTEND_URL)
    
    page.locator(".url-input").fill("https://youtube.com/something")
    
    page.locator(".new-analysis-btn").click()

    expect(page.locator(".url-input")).to_have_value("")