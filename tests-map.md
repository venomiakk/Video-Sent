## Mapowanie przypadków testowych na kod źródłowy

Poniższa tabela przedstawia powiązanie logicznych przypadków testowych z ich fizyczną implementacją w kodzie projektu.

| ID Testu       | Plik testowy                        | Metoda / Test                                  |
| :------------- | :---------------------------------- | :--------------------------------------------- |
| **TC-ST1-001** | `test_analysis_ui.py`               | `test_analysis_input_interaction`              |
| **TC-ST1-002** | `test_analysis_ui.py`               | `test_analysis_validation_empty_url`           |
| **TC-ST2-001** | `test_downloader.py`                | `test_download_audio_download_and_create_file` |
| **TC-ST3-001** | `test_transcription.py`             | `test_transcribe_video_new_and_unlink_error`   |
| **TC-ST3-002** | `test_transcription.py`             | `test_transcribe_video_cached`                 |
| **TC-ST4-001** | `test_sentiment.py`                 | `test_analyze_success`                         |
| **TC-ST4-002** | `test_sentiment.py`                 | `test_analyze_api_error`                       |
| **TC-ST5-001** | `test_core.py`                      | `test_sentiment_keywords`                      |
| **TC-ST6-001** | `test_transcription.py`             | `test_transcribe_video_new_and_unlink_error`   |
| **TC-ST7-001** | `test_analysis_ui.py`               | `test_dashboard_structure`                     |
| **TC-ST8-001** | `api_tests.postman_collection.json` | Request: `Register - Success`                  |
| **TC-ST8-002** | `api_tests.postman_collection.json` | Request: `Transcribe - Bad URL Scheme`         |
