# Text Summarizer

A modern web application that provides text summarization capabilities with both guest and authenticated user features.

## Features

### Summarization
- Three summary length options: Short, Medium, Long
- Bullet points formatting option
- Support for both Turkish and English texts
- Copy summary to clipboard
- Local summarization algorithm with NLP
- ChatGPT integration (when available)

### User System
- Guest access with limited features
- User registration and authentication
- Summary history for registered users
- Delete saved summaries

### Interface
- Modern, responsive design
- User-friendly notifications
- Clean and intuitive UI
- Mobile-friendly layout

## Guest vs Registered Users

### Guest Features
- Access to medium-length summarization
- View all options (some disabled)
- No history saving
- No bullet points feature

### Registered User Features
- All summary length options (Short, Medium, Long)
- Bullet points formatting
- Save summaries to history
- View and manage summary history
- Delete saved summaries

## Technical Details

### Built With
- Django 4.2.7
- NLTK 3.8.1
- Bootstrap 5
- Font Awesome
- Modern JavaScript

### Requirements
- Python 3.8+
- NLTK
- Django
- requests

## Installation

1. Clone the repository
```bash
git clone https://github.com/alperencbn05/TextSummarizer.git
cd TextSummarizer
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Apply migrations
```bash
python manage.py migrate
```

4. Run the development server
```bash
python manage.py runserver
```

5. Visit http://localhost:8000 in your browser

## Usage

1. Access the site
   - As a guest: Click "Continue as Guest"
   - As a user: Register or Login

2. Enter text to summarize
   - Paste or type your text
   - Select summary length (Medium only for guests)
   - Choose bullet points (registered users only)

3. Get your summary
   - Click "Summarize"
   - Copy the result using the copy button
   - View in history (registered users only)

## Future Improvements

- PDF text extraction
- URL summarization
- OCR capabilities
- Additional language support
- API endpoints
- Advanced NLP features
- User profiles
- Summary sharing
- Categories for summaries

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Alperen Çoban

## Acknowledgments

- NLTK library for text processing
- Bootstrap for the UI components
- Font Awesome for icons

## Example Usage

Input text:
```
Artificial Intelligence (AI) is revolutionizing the way we live and work in the modern world. Machine learning, a subset of AI, enables computers to learn from data and improve their performance over time. Deep learning, which uses neural networks inspired by the human brain, has achieved remarkable success in tasks like image recognition and natural language processing.
```

The system will generate a concise summary highlighting the most important sentences. 