#!/bin/bash

# Crear y activar el entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar los requisitos
pip install -r requirements.txt

# Ejecutar el script de prueba
python test.py
