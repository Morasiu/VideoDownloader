# How to use

1. Install Python 3.8+
1. Install `pipenv`
    ```bash
    pip install pipenv
    ```
1. Sync to download packages
    ```bash
    pipenv sync
    ```
1. Check config in `Download.py`
    ```python
    DOWNLOAD_PATH = "./download/"
    DOWNLOAD_FILLERS = True
    URL = "https://ft.wbijam.pl/ps.html"
    ```
1. Run scirpt 
    ```bash
    pipenv run python .\Download.py
    ```