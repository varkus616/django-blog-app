from django import forms
from .models import Post, UserProfile, Message
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'text',)


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')


class ProfileForm(forms.ModelForm):
    birth_date = forms.DateField(widget=forms.SelectDateWidget(years=range(1900, 2025)))

    class Meta:
        model = UserProfile
        fields = ('birth_date', )


class SendMessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ('subject', 'body')

