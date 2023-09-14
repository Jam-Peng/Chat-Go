from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import Room, Topic, Message
from .forms import RoomForm


def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:    # 如果已經登入，想要使用手動進入login/頁面，就會被重新導回首頁
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, "帳號不存在")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "帳號或密碼錯誤")

    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)     # 註冊後直接進行登入
            return redirect('home')
        else:
            messages.error(request, "帳號已註冊")

    return render(request, 'base/login_register.html', {'form': form})


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q) 
        )
    
    topics = Topic.objects.all()
    room_count = rooms.count()
    # 取得篩選使用者的訊息狀態
    room_messages = Message.objects.filter(
        Q(room__topic__name__icontains=q) 
    )

    context = {'rooms': rooms, 'topics': topics, 'room_count': room_count,
                'room_messages': room_messages}
    return render(request, 'base/home.html', context)


def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()     # 取得當前聊天室中所有訊息
    participants = room.participants.all()     # 取得所有當前聊天室中參與聊天的參與者

    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body')
        )
        room.participants.add(request.user)    # 只要留言就將使用者加到參與者區域
        return redirect('room', pk=room.id)    # 建立完留言重新導回當前聊天室 - 重整整理渲染頁面
    
    context = {'room': room, 'room_messages': room_messages, 'participants': participants}
    return render(request, 'base/room.html', context)


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()                # 取得當前使用者建立的聊天室
    room_messages = user.message_set.all()     # 取得當前使用者建立的訊息
    topics = Topic.objects.all()

    context = {'user': user, 'rooms': rooms, 'room_messages': room_messages, 'topics': topics}
    return render(request, 'base/profile.html', context)


# 刪除聊天室中的訊息
@login_required(login_url='/login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    # 使用者判斷 - 必須為使用者建立的訊息才可以進行刪除
    if request.user != message.user:
        return HttpResponse('沒有權限可進行刪除')
    
    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': message})


# 新增聊天室 - 將 Django 管理員的表單拉到瀏覽器上使用
# @login_required 
@login_required(login_url='/login')
def createRoom(request):
    form = RoomForm()
    if request.method == 'POST':
        # print(request.POST)          # 檢視取得表單傳送的資料
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.host = request.user
            room.save()
            return redirect('home')

    context = {'form': form}
    return render(request, 'base/room_form.html', context)


# 更新聊天室資料
@login_required(login_url='/login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)     # 取得特定 id 的聊天室
    form = RoomForm(instance=room)     # 將原始的資料增加回到表單上
    
    # 使用者判斷 - 必須為使用者建立的物件才可以進行修改
    if request.user != room.host:
        return HttpResponse('沒有權限可進行更新')

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)   # 取得選取的聊天室資料
        if form.is_valid():
            form.save()
            return redirect('home')

    context = {'form': form}
    return render(request, 'base/room_form.html', context)


# 刪除聊天室
@login_required(login_url='/login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    # 使用者判斷 - 必須為使用者建立的物件才可以進行刪除
    if request.user != room.host:
        return HttpResponse('沒有權限可進行刪除')
    
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})


