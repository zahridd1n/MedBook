from django import forms
from .models import BlogPost, BlogComment


class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'excerpt', 'featured_image', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Blog nomi'}),
            'excerpt': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Qisqa matn (ixtiyoriy)',
                'rows': 3
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Blog mazmuni',
                'rows': 10
            }),
            'featured_image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BlogCommentForm(forms.ModelForm):
    class Meta:
        model = BlogComment
        fields = ['name', 'email', 'content']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ismingiz'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Fikringiz',
                'rows': 4
            }),
        }
