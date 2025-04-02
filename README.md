# Text Summarizer

A web application that summarizes text using natural language processing techniques. The application supports both English and Turkish text summarization.

## Features

- Text summarization in English and Turkish
- Adjustable summary length (short, medium, long)
- Option to display summary as bullet points
- Modern and responsive UI
- Automatic language detection

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/text-summarizer.git
cd text-summarizer
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Run the development server:
```bash
python manage.py runserver
```

5. Open your browser and navigate to `http://127.0.0.1:8000/`

## Usage

1. Enter or paste the text you want to summarize in the text area
2. Select the desired summary length
3. Choose whether to display the summary as bullet points
4. Click the "Summarize" button
5. View the generated summary

## Technologies Used

- Python 3.x
- Django
- NLTK
- Bootstrap 5
- Font Awesome

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

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

## Contributing

Feel free to submit issues and enhancement requests! 