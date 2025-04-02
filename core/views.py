from django.shortcuts import render
from .forms import TextForm
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from string import punctuation
import re

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

def is_turkish_text(text):
    """Check if the text contains Turkish characters."""
    turkish_chars = set('çÇğĞıİöÖşŞüÜ')
    return any(char in turkish_chars for char in text)

def get_stop_words():
    """Get stop words for both English and Turkish."""
    stop_words = set(stopwords.words('english'))
    turkish_stop_words = {
        'acaba', 'ama', 'aslında', 'az', 'bazı', 'belki', 'biri', 'birkaç', 'birşey',
        'biz', 'bu', 'çok', 'çünkü', 'da', 'daha', 'de', 'defa', 'diye', 'eğer', 'en',
        'gibi', 'hem', 'hep', 'hepsi', 'her', 'hiç', 'için', 'ile', 'ise', 'kez', 'ki',
        'kim', 'mı', 'mu', 'mü', 'nasıl', 'ne', 'neden', 'nerde', 'nerede', 'nereye',
        'niçin', 'niye', 'o', 'sanki', 'şey', 'siz', 'şu', 'tüm', 've', 'veya', 'ya',
        'yani'
    }
    stop_words.update(turkish_stop_words)
    stop_words.update(punctuation)
    return stop_words

def summarize_text(text, bullet_points=False, summary_length='medium'):
    """Summarize the given text."""
    # Determine if text is Turkish
    is_turkish = is_turkish_text(text)
    
    # Split into sentences based on language
    if is_turkish:
        # Turkish sentence delimiters
        sentences = re.split(r'[.!?]+', text)
    else:
        sentences = sent_tokenize(text)
    
    # Clean sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Tokenize words and calculate frequencies
    words = word_tokenize(text.lower())
    stop_words = get_stop_words()
    words = [word for word in words if word not in stop_words]
    word_freq = FreqDist(words)
    
    # Calculate sentence scores
    sentence_scores = {}
    for sentence in sentences:
        for word in word_tokenize(sentence.lower()):
            if word in word_freq:
                if sentence not in sentence_scores:
                    sentence_scores[sentence] = word_freq[word]
                else:
                    sentence_scores[sentence] += word_freq[word]
    
    # Select top sentences based on summary length
    num_sentences = len(sentences)
    if summary_length == 'short':
        select_count = max(1, num_sentences // 4)
    elif summary_length == 'long':
        select_count = max(2, num_sentences // 2)
    else:  # medium
        select_count = max(1, num_sentences // 3)
    
    summary_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:select_count]
    summary_sentences = [s[0] for s in sorted(summary_sentences, key=lambda x: sentences.index(x[0]))]
    
    # Format summary
    if bullet_points:
        return '\n'.join(f'• {s}' for s in summary_sentences)
    return ' '.join(summary_sentences)

def home(request):
    if request.method == 'POST':
        form = TextForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            bullet_points = form.cleaned_data['bullet_points']
            summary_length = form.cleaned_data['summary_length']
            
            try:
                summary = summarize_text(text, bullet_points, summary_length)
                return render(request, 'core/home.html', {
                    'form': form,
                    'summary': summary,
                    'bullet_points': bullet_points
                })
            except Exception as e:
                return render(request, 'core/home.html', {
                    'form': form,
                    'error': str(e)
                })
    else:
        form = TextForm()
    
    return render(request, 'core/home.html', {'form': form})
