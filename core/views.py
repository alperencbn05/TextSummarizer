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
import math
from collections import defaultdict
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

def calculate_tf_idf(sentences):
    """Calculate TF-IDF scores for words in sentences."""
    stop_words = get_stop_words()
    word_freq = defaultdict(int)
    word_doc_freq = defaultdict(int)
    
    # Count word frequencies and document frequencies
    for sentence in sentences:
        words = [word.lower() for word in re.findall(r'\b\w+\b', sentence) 
                if word.lower() not in stop_words and len(word) > 2]
        unique_words = set(words)
        
        for word in words:
            word_freq[word] += 1
        for word in unique_words:
            word_doc_freq[word] += 1
    
    # Calculate TF-IDF scores
    tf_idf_scores = {}
    num_sentences = len(sentences)
    
    for word, freq in word_freq.items():
        tf = freq / sum(word_freq.values())
        idf = math.log(num_sentences / (word_doc_freq[word] + 1))
        tf_idf_scores[word] = tf * idf
    
    return tf_idf_scores

def summarize_text(text, bullet_points=False, summary_length='medium'):
    """Summarize the given text using TF-IDF and improved sentence scoring."""
    # Clean and preprocess text
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split into sentences properly
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return ""
    
    # Calculate TF-IDF scores
    tf_idf_scores = calculate_tf_idf(sentences)
    
    # Calculate sentence scores
    sentence_scores = {}
    for sentence in sentences:
        # Get words in sentence
        words = [word.lower() for word in re.findall(r'\b\w+\b', sentence) 
                if word.lower() not in get_stop_words() and len(word) > 2]
        
        # Calculate sentence score based on TF-IDF
        tf_idf_score = sum(tf_idf_scores.get(word, 0) for word in words)
        
        # Position score (earlier sentences are more important)
        position = sentences.index(sentence)
        position_score = 1.0 / (position + 1)
        
        # Length score (prefer medium-length sentences)
        length_score = 1.0 - abs(len(words) - 10) / 20  # Peak at 10 words
        
        # Combine scores with weights
        total_score = (0.5 * tf_idf_score) + (0.3 * position_score) + (0.2 * length_score)
        sentence_scores[sentence] = total_score
    
    # Select number of sentences based on length
    num_sentences = len(sentences)
    if summary_length == 'short':
        select_count = max(2, num_sentences // 5)  # 20% of sentences
    elif summary_length == 'long':
        select_count = max(4, num_sentences // 2)  # 50% of sentences
    else:  # medium
        select_count = max(3, num_sentences // 3)  # 33% of sentences
    
    # Get top sentences and sort by original position
    summary_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:select_count]
    summary_sentences = [s[0] for s in summary_sentences]
    summary_sentences.sort(key=lambda x: sentences.index(x))
    
    # Format output based on bullet points
    if bullet_points:
        # Group related sentences into bullet points
        bullet_points_list = []
        current_point = []
        
        # Calculate average sentence score for grouping
        avg_score = sum(sentence_scores[s] for s in summary_sentences) / len(summary_sentences)
        
        for sentence in summary_sentences:
            current_point.append(sentence)
            
            # Create new bullet point if:
            # 1. We have 2 or more sentences and current sentence score is significantly different
            # 2. We have 3 sentences (max per bullet point)
            # 3. This is the last sentence
            if (len(current_point) >= 2 and sentence_scores[sentence] < avg_score * 0.8) or \
               len(current_point) >= 3 or \
               sentence == summary_sentences[-1]:
                # Clean up the bullet point text
                point_text = ' '.join(current_point)
                point_text = re.sub(r'\s+', ' ', point_text).strip()
                bullet_points_list.append('• ' + point_text)
                current_point = []
        
        # If we still have sentences in current_point, add them as the last bullet point
        if current_point:
            point_text = ' '.join(current_point)
            point_text = re.sub(r'\s+', ' ', point_text).strip()
            bullet_points_list.append('• ' + point_text)
        
        return '\n'.join(bullet_points_list)
    else:
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

def is_meaningful_text(text):
    """Check if the text is meaningful enough to summarize."""
    # Count words
    words = [w for w in text.split() if w.strip()]
    
    # Check if text has at least 3 words
    return len(words) >= 3

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
                messages.error(request, 'Could not generate a summary. Please try with different text.')
                return render(request, 'core/home.html', context)
            
            # Add summary to context
            context['summary_text'] = summary_text
            return render(request, 'core/home.html', context)
            
        except Exception as e:
            messages.error(request, 'An error occurred while generating the summary. Please try again.')
            return render(request, 'core/home.html', context)

    return render(request, 'core/home.html', context)

def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')
