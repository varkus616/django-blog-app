from django.contrib import admin
from .models import Post, UserProfile, Message

admin.site.register(Post)
admin.site.register(UserProfile)
admin.site.register(Message)