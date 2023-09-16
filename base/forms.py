from django.forms import ModelForm
from .models import Room, User
# from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class RoomForm(ModelForm):
    class Meta:
      model = Room
      fields = '__all__'
      exclude = ['host', 'participants']


# 更新使用者的 Form表單模型
class UserForm(ModelForm):
    class Meta:
      model = User
      fields = ['avatar', 'name', 'username', 'email', 'bio']


# 使用者註冊的 Form表單模型
class MyUserCreationForm(UserCreationForm):
    class Meta:
      model = User
      fields = ['name', 'username', 'email', 'password1', 'password2']
