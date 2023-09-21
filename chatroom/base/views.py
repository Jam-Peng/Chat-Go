from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm


def loginPage(request):
    page = 'login'
    login_message = ""

    if request.user.is_authenticated:      # 如果已經登入，想要使用手動進入login/頁面，就會被重新導回首頁
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        user = User.objects.filter(email=email)

        if email == "" or password == "":
            login_message = "帳號和密碼不能留空"
        elif not user:
            login_message = "帳號或密碼錯誤"
        else:
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('home') 
            else:
                login_message = "帳號或密碼錯誤" 

    context = {'page': page, 'login_message': login_message}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    form = MyUserCreationForm()

    sigin_message = ""
    if request.method == 'POST':
        username = request.POST.get("username")
        email = request.POST.get("email").lower()
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if username == '' and email == '' and password1 == '' and password2 == '':
            sigin_message = "請正確填寫資料"
        if password1 != password2:
            sigin_message = "請確認密碼相同"
        elif User.objects.filter(email = email):
            sigin_message = "帳號已註冊"
        else:
            user = User.objects.create_user(
                username = username, 
                email = email, 
                password = password1
            )
            user.save()
            login(request, user)     
            return redirect('home')

    return render(request, 'base/login_register.html', {'form': form, 'sigin_message': sigin_message})


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q) 
        )
    
    topics = Topic.objects.all()[0:5]
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
    room_messages = room.message_set.all()        # 取得當前聊天室中所有訊息
    participants = room.participants.all()        # 取得所有當前聊天室中參與聊天的參與者

    room_message = ''
    if request.method == 'POST':
        body = request.POST.get('body')

        if body is '':
            room_message = '無法傳送空白留言'
        else:
            message = Message.objects.create(
                user = request.user,
                room = room,
                body = request.POST.get('body')
            )

            room.participants.add(request.user)    # 只要留言就將使用者加到參與者區域
            return redirect('room', pk=room.id)    # 建立完留言重新導回當前聊天室 - 重整整理渲染頁面
    
    context = {'room': room, 'room_messages': room_messages, 'participants': participants, 'room_message': room_message}
    return render(request, 'base/room.html', context)


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()                    # 取得當前使用者建立的聊天室
    room_messages = user.message_set.all()         # 取得當前使用者建立的訊息
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
@login_required(login_url='/login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()                   # 加入自定義樣式，所以改寫取得 topic值方式

    if request.method == 'POST':
        topic_name = request.POST.get('topic')                            # 取 from表單的 name屬性值
        topic, created = Topic.objects.get_or_create(name=topic_name)     # 建立一個新的或取舊的 Topic 物件

        # 建立聊天室
        Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST.get('name'),                    # 這裡的 name是指取得 {{form.name}}
            description = request.POST.get('description'),      # 這裡的 description是指取得 {{form.description}}
        )

        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)


# 更新聊天室資料
@login_required(login_url='/login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)                   # 取得特定 id 的聊天室
    form = RoomForm(instance=room)                   # 將原始的資料增加回到表單上
    topics = Topic.objects.all()                     # 加入樣式，所以改寫取得topic資料方式
    
    old_topic = Topic.objects.get(name=room.topic)   # 原本的主題

    # 使用者判斷 - 必須為使用者建立的物件才可以進行修改
    if request.user != room.host:
        return HttpResponse('沒有權限可進行更新')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')                           # 取 from表單的 name屬性值
        topic, created = Topic.objects.get_or_create(name=topic_name)    # 建立一個新的或取舊的 Topic 物件

        # 更新聊天室的值
        if topic != old_topic:                       # 如果新的主題和舊的主題不一樣，就先進行刪除舊的
            old_topic.delete()
        room.topic= topic
        room.name = request.POST.get('name')
        room.description = request.POST.get('description')
        room.save()

        return redirect('home')

    context = {'form': form, 'topics': topics, 'room': room}
    return render(request, 'base/room_form.html', context)


# 刪除聊天室
@login_required(login_url='/login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    topic = Topic.objects.get(name=room.topic)

    # 使用者判斷 - 必須為使用者建立的物件才可以進行刪除
    if request.user != room.host:
        return HttpResponse('沒有權限可進行刪除')
    
    if request.method == 'POST':
        room.delete()
        topic.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})


# 更新使用者
@login_required(login_url='login')
def updateUser(request):
    user = request.user                     # 取得當前使用者
    form = UserForm(instance=user)          # 將當前使用者資料加到表單上

    # 使用自定義的表單取值更新
    if request.method == 'POST':
        form.name = request.POST.get('name')
        form.username = request.POST.get('username')
        form.email = request.POST.get('email')
        form.bio = request.POST.get('bio')
        form = UserForm(request.POST, request.FILES, instance=user)

        form.save()
        return redirect('user-profile', pk=user.id)
    
    return render(request, 'base/update_user.html', {'form': form, 'user': user})


# 聊天室所有主題搜尋
@login_required(login_url='login')
def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {'topics': topics})


# 手機版 - 所有最新留言
def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages': room_messages})