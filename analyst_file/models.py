from django.db import models

from analysts.models import Analyst


# Create your models here.

class AnalystFile(models.Model):
    filename = models.CharField(max_length=100)
    file_type = models.CharField(max_length=100)
    upload = models.FileField(upload_to='analyst_file')
    analyst = models.ForeignKey(Analyst,on_delete=models.CASCADE,related_name='files')
    created_at = models.DateTimeField(auto_now_add=True)
    scanner_source = models.CharField(max_length=100, default='manual')


    def __str__(self):
        return self.filename

    @property
    def is_xml(self):
        """Check if this file is an XML file based on filename or content type"""
        return (
            self.file_type.lower() in ['text/xml', 'application/xml'] or 
            self.filename.lower().endswith('.xml')
        )
