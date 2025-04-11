from django import forms
from .models import Regulation, Department, Article
from django.db import models
from datetime import datetime

class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'content', 'type', 'reference']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'reference': 'Enter a reference number for the article (e.g., 1, 1.1, 1.2)',
        }

ArticleFormSet = forms.inlineformset_factory(
    Regulation, 
    Article, 
    form=ArticleForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False
)

class RegulationForm(forms.ModelForm):
    assigned_departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Select at least one department"
    )

    class Meta:
        model = Regulation
        fields = ['name', 'reference', 'description', 'type', 'status', 'assigned_departments', 'issue_date', 'effective_date', 'expiry_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'assigned_departments': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'effective_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        help_texts = {
            'name': 'Enter a clear and descriptive name for the regulation',
            'reference': 'Enter a unique reference number for the regulation (e.g., REG-2024-001)',
            'description': 'Provide a detailed description of the regulation\'s purpose and scope',
            'type': 'Select the type of document',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'form-control'})
        self.fields['reference'].widget.attrs.update({'class': 'form-control'})
        self.fields['description'].widget.attrs.update({'class': 'form-control'})
        self.fields['type'].widget.attrs.update({'class': 'form-control'})
        
        # Generate the next reference number if this is a new regulation
        if not self.instance.pk:
            # Get the maximum reference number
            max_ref = Regulation.objects.aggregate(max_ref=models.Max('reference'))['max_ref']
            if max_ref:
                # Extract the number part and increment it
                try:
                    ref_num = int(max_ref.split('-')[-1])
                    next_num = ref_num + 1
                    # Format the new reference number
                    year = datetime.now().year
                    self.initial['reference'] = f'REG-{year}-{next_num:03d}'
                except (ValueError, IndexError):
                    # If parsing fails, use a default format
                    self.initial['reference'] = f'REG-{datetime.now().year}-001'
            else:
                # If no regulations exist yet, start with 001
                self.initial['reference'] = f'REG-{datetime.now().year}-001'

class RegulationEditForm(RegulationForm):
    """Form for editing existing regulations."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields read-only if regulation is not in draft or rejected status
        if self.instance and self.instance.status not in ['draft', 'rejected']:
            for field in self.fields:
                self.fields[field].widget.attrs['readonly'] = True
                self.fields[field].widget.attrs['disabled'] = True 