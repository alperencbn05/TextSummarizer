from django import forms

class TextForm(forms.Form):
    text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Paste your text here...',
            'rows': 5
        }),
        label='Enter your text:'
    )
    summary_length = forms.ChoiceField(
        choices=[
            ('short', 'Very Concise'),
            ('medium', 'Balanced'),
            ('long', 'Detailed')
        ],
        initial='medium',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Summary Length:'
    )
    bullet_points = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Show as bullet points'
    ) 