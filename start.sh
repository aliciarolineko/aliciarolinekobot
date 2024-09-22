mkdir server
python3 -m http.server -d server &
cd server
pip install -r requirements.txt
python3 ../neko.py
#!/bin/bash
