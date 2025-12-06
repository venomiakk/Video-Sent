from locust import HttpUser, task, between
import random

class VideoSentimentUser(HttpUser):
    wait_time = between(1, 5)
    token = None

    def on_start(self):
        """Uruchamia się raz dla każdego 'użytkownika' przy starcie - tutaj logowanie."""
        random_id = random.randint(1, 1000000)
        email = f"loadtest_{random_id}@test.com"
        password = "password123"

        self.client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password
        })

        response = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    @task(3) 
    def health_check(self):
        """Lekki test - sprawdzenie czy serwer żyje"""
        self.client.get("/")

    @task(1) 
    def check_invalid_auth(self):
        """Sprawdzenie jak serwer radzi sobie z błędami autoryzacji"""
        self.client.get("/api/v1/auth/test") 

    # @task(1) 
    # def process_video(self):
    #     if self.token:
    #         headers = {"Authorization": f"Bearer {self.token}"}
    #         self.client.post("/api/v1/transcribe/process", json={
    #             "url": "https://www.youtube.com/shorts/c7SRzIUjVYw",
    #             "model": "deepgram-nova-2"
    #         }, headers=headers)