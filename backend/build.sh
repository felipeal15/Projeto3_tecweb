#!/usr/bin/env bash
# Build do backend no Render (Build Command: bash build.sh).
# Instala as dependências, junta os arquivos estáticos do /admin e aplica as migrações.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
