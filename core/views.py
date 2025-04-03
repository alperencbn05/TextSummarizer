from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import TextForm
from .models import Summary
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from string import punctuation
import re
import random

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('averaged_perceptron_tagger')

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
        # Turkish sentence delimiters - use regex instead of NLTK
        sentences = re.split(r'[.!?]+', text)
    else:
        try:
            sentences = sent_tokenize(text)
        except:
            # Fallback to regex if NLTK tokenizer fails
            sentences = re.split(r'[.!?]+', text)
    
    # Clean sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Tokenize words and calculate frequencies
    try:
        words = word_tokenize(text.lower())
    except:
        # Fallback to simple word splitting if NLTK tokenizer fails
        words = re.findall(r'\b\w+\b', text.lower())
    
    stop_words = get_stop_words()
    words = [word for word in words if word not in stop_words]
    word_freq = FreqDist(words)
    
    # Calculate sentence scores
    sentence_scores = {}
    for sentence in sentences:
        for word in re.findall(r'\b\w+\b', sentence.lower()):
            if word in word_freq:
                if sentence not in sentence_scores:
                    sentence_scores[sentence] = word_freq[word]
                else:
                    sentence_scores[sentence] += word_freq[word]
    
    # Add randomness to sentence scores
    for sentence in sentence_scores:
        # Add a random factor between 0.5 and 1.5 to each sentence score
        random_factor = random.uniform(0.5, 1.5)
        sentence_scores[sentence] *= random_factor
    
    # Select top sentences based on summary length
    num_sentences = len(sentences)
    if summary_length == 'short':
        select_count = max(1, num_sentences // 4)
    elif summary_length == 'long':
        select_count = max(2, num_sentences // 2)
    else:  # medium
        select_count = max(1, num_sentences // 3)
    
    # Add more randomness to the number of sentences selected
    select_count = max(1, int(select_count * random.uniform(0.7, 1.3)))
    
    # Get all sentences with their scores
    all_sentences = list(sentence_scores.items())
    
    # Shuffle all sentences first
    random.shuffle(all_sentences)
    
    # Then sort by score
    all_sentences = sorted(all_sentences, key=lambda x: x[1], reverse=True)
    
    # Take top sentences
    summary_sentences = all_sentences[:select_count]
    
    # Extract just the sentences
    summary_sentences = [s[0] for s in summary_sentences]
    
    # Format summary
    if bullet_points:
        return '\n'.join(f'• {s}' for s in summary_sentences)
    return ' '.join(summary_sentences)

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
        else:
            messages.error(request, 'Registration failed. Please correct the errors.')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('home')
        messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

@login_required
def history_view(request):
    summaries = Summary.objects.filter(user=request.user)
    return render(request, 'core/history.html', {'summaries': summaries})

@login_required
def delete_summary(request, summary_id):
    try:
        summary = Summary.objects.get(id=summary_id, user=request.user)
        summary.delete()
        messages.success(request, 'Summary deleted successfully.')
    except Summary.DoesNotExist:
        messages.error(request, 'Summary not found.')
    return redirect('history')

def home(request):
    if request.method == 'POST':
        form = TextForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['text']
            bullet_points = form.cleaned_data['bullet_points']
            summary_length = form.cleaned_data['summary_length']
            
            try:
                summary = summarize_text(text, bullet_points, summary_length)
                
                # Save summary if user is logged in
                if request.user.is_authenticated:
                    Summary.objects.create(
                        user=request.user,
                        original_text=text,
                        summary_text=summary,
                        bullet_points=bullet_points,
                        summary_length=summary_length
                    )
                
                return render(request, 'core/home.html', {
                    'form': form,
                    'summary': summary,
                    'original_text': text,
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

def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')
