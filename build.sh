#!/bin/bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Initialize Hugging Face model
python -c "from transformers import AutoTokenizer, AutoModelForSeq2SeqGeneration; tokenizer = AutoTokenizer.from_pretrained('facebook/mbart-large-50-many-to-many-mmt'); model = AutoModelForSeq2SeqGeneration.from_pretrained('facebook/mbart-large-50-many-to-many-mmt')"

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create superuser if it doesn't exist
python manage.py createsuperuser --noinput --username admin --email admin@example.com 