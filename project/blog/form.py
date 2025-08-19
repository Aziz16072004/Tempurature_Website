from django import forms
from .models import User
class UserSignInForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'password']
        widgets = {
           
            'email': forms.TextInput(attrs={'class': 'input-field'}),
            'password': forms.PasswordInput(attrs={'class': 'input-field'}),
        }
class UserSignUpForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['fullName','email', 'password']
        widgets = {
            'fullName': forms.TextInput(attrs={'class': 'input-field'}),
            'email': forms.TextInput(attrs={'class': 'input-field'}),
            'password': forms.PasswordInput(attrs={'class': 'input-field'}),
        }
class ContactForm(forms.Form):
   
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)

    def send_email(self):
        print(f"Sending email from {self.cleaned_data['email']} with message: {self.cleaned_data['message']}")