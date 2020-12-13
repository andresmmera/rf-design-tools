from django.db import models
from django.urls import reverse

class Tool(models.Model):
    """A typical class defining a model, derived from the Model class."""

    # Fields
    title = models.CharField(max_length=50, help_text='Tool name')
    description = models.TextField(max_length=100, help_text='Tool description')
    html_file  =models.CharField(max_length=50, help_text='html')

    # Methods
    def __str__(self):
        """String for representing the Model object."""
        return self.title
    
    def get_absolute_url(self):
        """Returns the url to access a detail record for this book."""
        return reverse('tool-detail', args=[str(self.html_file)])