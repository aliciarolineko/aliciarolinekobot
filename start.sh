mkdir server
python3 -m http.server -d server &
pip install -r requirements.txt
python3 neko.py
#!/bin/bash
