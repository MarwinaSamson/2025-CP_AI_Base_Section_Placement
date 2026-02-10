from django import forms
from .models import SectionMasterlist

class SectionMasterlistUploadForm(forms.ModelForm):
    class Meta:
        model = SectionMasterlist
        fields = ['program', 'section', 'file']

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file and not file.name.lower().endswith('.pdf'):
            raise forms.ValidationError('Only PDF files are allowed.')
        return file
