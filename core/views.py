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
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import os
from django.http import JsonResponse

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('averaged_perceptron_tagger')

# Initialize the model and tokenizer
tokenizer = None
model = None
summarizer = None

def load_model():
    """Load the model only when needed."""
    global tokenizer, model, summarizer
    if summarizer is None:
        try:
            model_name = "facebook/mbart-large-50-many-to-many-mmt"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name, device_map='auto', low_cpu_mem_usage=True)
            summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)
        except Exception as e:
            print(f"Model loading error: {e}")
            return False
    return True

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
    """Summarize the given text using Hugging Face's Turkish model."""
    # Clean and preprocess text
    text = re.sub(r'\s+', ' ', text).strip()
    
    if not text:
        return ""
    
    try:
        # Try using Hugging Face model first
        if load_model() and summarizer is not None:
            # Set max length based on summary_length parameter
            if summary_length == 'short':
                max_length = 50
            elif summary_length == 'long':
                max_length = 150
            else:  # medium
                max_length = 100
            
            # Generate summary
            summary = summarizer(text, max_length=max_length, min_length=30, do_sample=False)[0]['summary_text']
            
            # Format as bullet points if requested
            if bullet_points:
                # Split into sentences and clean them
                sentences = re.split(r'[.!?]+', summary)
                sentences = [s.strip() for s in sentences if s.strip()]
                
                # Format each sentence as a bullet point
                bullet_points_list = ['• ' + sentence for sentence in sentences]
                return '\n'.join(bullet_points_list)
            else:
                return summary
        else:
            # Fallback to NLTK if model loading fails
            return summarize_text_nltk(text, bullet_points, summary_length)
            
    except Exception as e:
        print(f"Summarization error: {e}")
        # Fallback to NLTK if there's an error
        return summarize_text_nltk(text, bullet_points, summary_length)

def summarize_text_nltk(text, bullet_points=False, summary_length='medium'):
    """Generate a summary using NLTK as fallback."""
    # Tokenize the text into sentences
    sentences = sent_tokenize(text)
    
    # Remove special characters and convert to lowercase
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # Tokenize words
    words = word_tokenize(text)
    
    # Remove stopwords and punctuation
    stop_words = get_stop_words()
    words = [word for word in words if word not in stop_words]
    
    # Calculate word frequencies
    word_freq = defaultdict(int)
    for word in words:
        word_freq[word] += 1
    
    # Calculate sentence scores based on word frequencies
    sentence_scores = defaultdict(int)
    for sentence in sentences:
        for word in word_tokenize(sentence.lower()):
            if word in word_freq:
                sentence_scores[sentence] += word_freq[word]
    
    # Select top sentences based on summary length
    num_sentences = len(sentences)
    if summary_length == 'short':
        num_summary = max(1, num_sentences // 4)
    elif summary_length == 'long':
        num_summary = max(2, num_sentences // 2)
    else:  # medium
        num_summary = max(1, num_sentences // 3)
    
    # Get top sentences
    summary_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:num_summary]
    summary_sentences = [s[0] for s in summary_sentences]
    
    # Sort sentences by their original order
    summary_sentences.sort(key=lambda x: sentences.index(x))
    
    # Format as bullet points if requested
    if bullet_points:
        return '\n'.join(['• ' + sentence for sentence in summary_sentences])
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
    summaries = Summary.objects.filter(user=request.user).order_by('-created_at')
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

def summarize_text_api(request):
    if request.method == 'POST':
        text = request.POST.get('text', '')
        summary_length = request.POST.get('summary_length', 'medium')
        use_bullets = request.POST.get('use_bullets', 'false') == 'true'
        
        if not text:
            return JsonResponse({'error': 'Lütfen özetlenecek bir metin girin.'})
            
        if not load_model():
            return JsonResponse({'error': 'Model yüklenemedi. Lütfen daha sonra tekrar deneyin.'})
            
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
                summary_text = summarize_text(text, bullet_points=use_bullets, summary_length=summary_length)
                
                # Save summary for logged-in users
                Summary.objects.create(
                    user=request.user,
                    original_text=text,
                    summary_text=summary_text,
                    bullet_points=use_bullets,
                    summary_length=summary_length
                )
            
            if not summary_text.strip():
                return JsonResponse({'error': 'Özetlenemedi. Lütfen farklı bir metin deneyin.'})
            
            return JsonResponse({'summary': summary_text})
            
        except Exception as e:
            return JsonResponse({'error': 'Özetleme sırasında bir hata oluştu. Lütfen daha sonra tekrar deneyin.'})

    return JsonResponse({'error': 'Geçersiz istek.'})
