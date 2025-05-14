from django import forms

class XMLUploadForm(forms.Form):
    """
    Form for uploading two XML files:
    - source_file: The original XML file containing commands
    - error_file: The result XML file containing command status
    """
    source_file = forms.FileField(
        label='Source XML File',
        help_text='Upload the original XML file with commands',
        required=True,
        widget=forms.FileInput(attrs={'accept': '.xml'})
    )
    
    error_file = forms.FileField(
        label='Result XML File',
        help_text='Upload the result XML file containing command status',
        required=True,
        widget=forms.FileInput(attrs={'accept': '.xml'})
    )
    
    def clean(self):
        """Validate that both files are provided"""
        cleaned_data = super().clean()
        source_file = cleaned_data.get('source_file')
        error_file = cleaned_data.get('error_file')
        
        if not source_file:
            self.add_error('source_file', 'Source XML file is required')
        
        if not error_file:
            self.add_error('error_file', 'Result XML file is required')
            
        return cleaned_data
