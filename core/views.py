from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import TextForm
from .models import Summary, GuestUsage
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from string import punctuation
import re
import random
import requests
import json

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

def get_chatgpt_summary(text, length='medium'):
    """Get summary from ChatGPT free API."""
    try:
        # Free ChatGPT API endpoint
        url = "https://free.churchless.tech/v1/chat/completions"
        
        # Adjust prompt based on length
        if length == 'short':
            prompt = f"Summarize this text very briefly in 2-3 sentences: {text}"
        elif length == 'long':
            prompt = f"Provide a detailed summary of this text, covering all main points: {text}"
        else:  # medium
            prompt = f"Summarize this text in a balanced way, covering the key points: {text}"

        # Prepare the request
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that summarizes text."},
                {"role": "user", "content": prompt}
            ]
        }

        # Make the request with a shorter timeout
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        
        # Only proceed if we get a successful response
        if response.status_code == 200:
            result = response.json()
            summary = result['choices'][0]['message']['content'].strip()
            return summary
        
        return None
        
    except Exception as e:
        print(f"ChatGPT API Error: {str(e)}")
        return None

def summarize_text(text, bullet_points=False, summary_length='medium'):
    """Summarize the given text."""
    # Try ChatGPT first, but don't wait for it if it's slow
    try:
        summary = get_chatgpt_summary(text, summary_length)
        if summary:
            if bullet_points:
                return '\n'.join(f'• {s.strip()}' for s in summary.split('.') if s.strip())
            return summary
    except:
        pass
    
    # If ChatGPT fails or is slow, use the existing algorithm
    # Determine if text is Turkish
    is_turkish = is_turkish_text(text)
    
    # Split into sentences based on language
    if is_turkish:
        sentences = re.split(r'[.!?]+', text)
    else:
        try:
            sentences = sent_tokenize(text)
        except:
            sentences = re.split(r'[.!?]+', text)
    
    # Clean sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Tokenize words and calculate frequencies
    try:
        words = word_tokenize(text.lower())
    except:
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
    random.shuffle(all_sentences)
    all_sentences = sorted(all_sentences, key=lambda x: x[1], reverse=True)
    
    # Take top sentences
    summary_sentences = all_sentences[:select_count]
    summary_sentences = [s[0] for s in summary_sentences]
    summary = ' '.join(summary_sentences)

    # Format summary
    if bullet_points:
        summary = '\n'.join(f'• {s.strip()}' for s in summary.split('.') if s.strip())
    
    return summary

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

def is_meaningful_text(text):
    """Check if the text is meaningful enough to summarize."""
    # Count words (excluding common meaningless patterns)
    words = [w for w in text.split() if not w.replace('a', '').replace('s', '').replace('d', '').isspace()]
    
    # Check if text has at least 3 different words and 10 total words
    unique_words = set(words)
    return len(unique_words) >= 3 and len(words) >= 10

def home(request):
    context = {}
    
    # Check if user is accessing as guest
    if request.GET.get('guest') == 'true':
        messages.info(request, 'You are continuing as a guest. Login to access bullet points and save your summaries.')
    
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        summary_length = request.POST.get('summary_length', 'medium')
        bullet_points = request.POST.get('bullet_points') == 'on'
        
        # Force medium length for guests
        if not request.user.is_authenticated and summary_length != 'medium':
            summary_length = 'medium'
        
        # Store form data in context
        context.update({
            'original_text': text,
            'summary_length': summary_length,
            'bullet_points': bullet_points
        })
        
        if not text:
            messages.error(request, 'Please enter some text to summarize.')
            return render(request, 'core/home.html', context)

        if not is_meaningful_text(text):
            messages.error(request, 'Please enter meaningful text with at least 10 words to generate a summary.')
            return render(request, 'core/home.html', context)

        try:
            # Generate summary based on user type
            if not request.user.is_authenticated:
                # Track guest usage
                GuestUsage.objects.create(
                    ip_address=request.META.get('REMOTE_ADDR'),
                    timestamp=timezone.now()
                )
                
                # Generate summary for guest (without bullet points and force medium length)
                summary_text = summarize_text(text, bullet_points=False, summary_length='medium')
            else:
                # Generate summary for logged-in user (with all features)
                summary_text = summarize_text(text, bullet_points=bullet_points, summary_length=summary_length)
                
                # Save summary for logged-in users
                Summary.objects.create(
                    user=request.user,
                    original_text=text,
                    summary_text=summary_text,
                    bullet_points=bullet_points,
                    summary_length=summary_length
                )
            
            if not summary_text.strip():
                raise ValueError("Could not generate a meaningful summary.")
            
            # Add summary to context
            context['summary_text'] = summary_text
            return render(request, 'core/home.html', context)
            
        except Exception as e:
            messages.error(request, 'Could not generate a summary. Please check if your text is meaningful and try again.')
            return render(request, 'core/home.html', context)

    return render(request, 'core/home.html', context)

def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')
