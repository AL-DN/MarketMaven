# to overide forms
from django import forms
from .models import Post

# overides the form sidget
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['symbol','side','content']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        
        # sets fields 
        self.fields['symbol'].disabled = True
        self.fields['side'].disabled = True

    