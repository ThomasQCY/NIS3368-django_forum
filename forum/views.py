# coding:utf-8
import os
import time
import logging

from io import BytesIO

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.http.response import Http404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from forum.models import Nav, Post, Comment, Application, LoginUser, Notice, Column, Message


from .models import Paper


from forum.form import MessageForm, PostForm, LoginUserForm
from django.urls import reverse_lazy

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db.models import Q
from django.utils.timezone import now, timedelta
from django.core.cache import cache

from forum.validate import create_validate_code

logger = logging.getLogger(__name__)

PAGE_NUM = 50

#每个视图必须要做的只有两件事：
#返回一个包含被请求页面内容的 HttpResponse 对象，或者抛出一个异常，比如 Http404 。至于你还想干些什么，随便你。

def papers_list(request):
    papers = Paper.objects.all()
    emojis = ['😀', '😂', '🤔', '😍', '👍', '💥', '📘', '🔬']
    # Add random emoji to each paper
    papers_with_emojis = [(paper, random.choice(emojis)) for paper in papers]
    return render(request, 'papers/papers.html', {'papers_with_emojis': papers_with_emojis})
    
def get_online_ips_count():
    """统计当前在线人数（5分钟内，中间件实现于middle.py）"""
    online_ips = cache.get("online_ips", [])
    if online_ips:
        online_ips = cache.get_many(online_ips).keys()
        return len(online_ips)
    return 0


def get_forum_info():
    """获取 论坛信息，贴子数，用户数，昨日发帖数，今日发帖数"""
    # 请使用缓存
    oneday = timedelta(days=1)
    today = now().date()
    lastday = today - oneday
    todayend = today + oneday
    post_number = Post.objects.count()
    account_number = LoginUser.objects.count()

    lastday_post_number = cache.get('lastday_post_number', None)
    today_post_number = cache.get('today_post_number', None)

    if lastday_post_number is None:
        lastday_post_number = Post.objects.filter(
            created_at__range=[lastday, today]).count()
        cache.set('lastday_post_number', lastday_post_number, 60 * 60)

    if today_post_number is None:
        today_post_number = Post.objects.filter(
            created_at__range=[today, todayend]).count()
        cache.set('today_post_number', today_post_number, 60 * 60)

    info = {
        "post_number": post_number,
        "account_number": account_number,
        "lastday_post_number": lastday_post_number,
        "today_post_number": today_post_number
    }
    return info


def userlogin(request, template_name='login.html'):
    """用户登录"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        next = request.POST['next']

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            user.levels += 1  # 登录一次积分加 1
            user.save()
        return HttpResponseRedirect(next)
    else:
        next = request.GET.get('next', None)
        if next is None:
            next = reverse_lazy('index')
        return render(request, template_name, {'next': next})


def userlogout(request):
    """用户注销"""
    logout(request)
    return HttpResponseRedirect(reverse_lazy('index'))


def userregister(request):
    """用户注销"""
    if request.method == 'POST':
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")
        email = request.POST.get("email", "")

        form = LoginUserForm(request.POST)
        errors = []
        # 验证表单是否正确
        if form.is_valid():
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain
            title = u"欢迎来到 %s ！" % site_name
            message = u"你好！ %s ,感谢注册 %s ！\n\n" % (username, site_name) + \
                      u"请牢记以下信息：\n" + \
                      u"用户名：%s" % username + "\n" + \
                      u"邮箱：%s" % email + "\n" + \
                      u"网站：http://%s" % domain + "\n\n"
            from_email = None
            try:
                send_mail(title, message, from_email, [email])
            except Exception as e:
                logger.error(
                    u'用户注册邮件发送失败:username: %s, email: %s' % (username, email), exc_info=True)
                return HttpResponse(u"发送邮件错误!\n注册失败", status=500)

            new_user = form.save()
            user = authenticate(username=username, password=password)
            login(request, user)
        else:
            # 如果表单不正确,保存错误到errors列表中
            for k, v in form.errors.items():
                # v.as_text() 详见django.forms.util.ErrorList 中
                errors.append(v.as_text())

        return render(request, 'user_ok.html', {"errors": errors})

    else:
        # next = request.GET.get('next',None)
        # if next is None:
        # next = reverse_lazy('index')
        return render(request, 'register.html')


class BaseMixin(object):
    def get_context_data(self, *args, **kwargs):
        context = super(BaseMixin, self).get_context_data(**kwargs)
        try:
            context['nav_list'] = Nav.objects.all()
            context['column_list'] = Column.objects.all()[0:5]
            context['last_comments'] = Comment.objects.all().order_by(
                "-created_at")[0:10]
            if self.request.user.is_authenticated:
                k = Notice.objects.filter(
                    receiver=self.request.user, status=False).count()
                context['message_number'] = k

        except Exception as e:
            logger.error(u'[BaseMixin]加载基本信息出错', e)

        return context


class IndexView(BaseMixin, ListView):
    """首页"""
    model = Post
    queryset = Post.objects.all()
    #载入 polls/index.html 模板文件，并且向它传递一个上下文(context)。这个上下文是一个字典，它将模板内的变量映射为 Python 对象。
    template_name = 'index.html'
    context_object_name = 'post_list'
    paginate_by = PAGE_NUM  # 分页--每页的数目
        
    def get_context_data(self, **kwargs):
        kwargs['foruminfo'] = get_forum_info()
        kwargs['online_ips_count'] = get_online_ips_count()
        kwargs['hot_posts'] = self.queryset.order_by("-responce_times")[0:10]
        
        if self.request.user.is_authenticated:  # Check if the user is logged in
            user_obj = LoginUser.objects.get(username=self.request.user.username)
            like_relations = user_obj.user_relations.all()
            kwargs['like_posts'] = [like_relation.post for like_relation in like_relations]
        else:
            kwargs['like_posts'] = []  # If not authenticated, pass an empty list
        
        return super(IndexView, self).get_context_data(**kwargs)


def postdetail(request, post_pk):
    """帖子详细页面"""
    post_pk = int(post_pk)
    post = Post.objects.get(pk=post_pk)
    comment_list = post.comment_set.all()
    if request.user.is_authenticated:
        k = Notice.objects.filter(receiver=request.user, status=False).count()
    else:
        k = 0
    # 统计帖子的访问访问次数
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        ip = request.META['HTTP_X_FORWARDED_FOR']
    else:
        ip = request.META['REMOTE_ADDR']
    title = post.title
    visited_ips = cache.get(title, [])

    if ip not in visited_ips:
        post.view_times += 1
        post.save()
        visited_ips.append(ip)
    cache.set(title, visited_ips, 15 * 60)
    return render(request, 'post_detail.html', {
        'post': post,
        'comment_list': comment_list,
        'message_number': k
    })


def makefriend(request, sender, receiver):
    """加好友"""
    sender = LoginUser.objects.get(username=sender)
    receiver = LoginUser.objects.get(username=receiver)
    application = Application(sender=sender, receiver=receiver, status=0)
    application.save()
    return HttpResponse(
        "OK申请发送成功！%s-->%s;<a href='/'>返回</a>" % (sender, receiver))


@login_required(login_url=reverse_lazy('user_login'))
def shownotice(request):
    """消息通知"""
    notice_list = Notice.objects.filter(receiver=request.user, status=False)
    myfriends = LoginUser.objects.get(username=request.user).friends.all()
    User_obj = LoginUser.objects.get(username=request.user)
    return render(request, 'notice_list.html', {
        'user': User_obj,
        'notice_list': notice_list,
        'myfriends': myfriends
    })
#「载入模板，填充上下文，再返回由它生成的 HttpResponse 对象」是一个非常常用的操作流程。
# 于是 Django 提供了一个快捷函数（render），我们用它来重写 index() 视图：

def noticedetail(request, pk):
    """具体通知"""
    pk = int(pk)
    notice = Notice.objects.get(pk=pk)
    notice.status = True
    notice.save()
    if notice.type == 0:  # 评论通知
        post_id = notice.event.post.id
        return HttpResponseRedirect(
            reverse_lazy('post_detail', kwargs={"post_pk": post_id}))
    message_id = notice.event.id  # 消息通知
    return HttpResponseRedirect(
        reverse_lazy('message_detail', kwargs={"pk": message_id}))


def friendagree(request, pk, flag):
    """好友同意/拒绝（flag 1同意，2拒绝）"""
    flag = int(flag)
    pk = int(pk)
    entity = Notice.objects.get(pk=pk)
    entity.status = True
    application = entity.event
    application.status = flag

    application.receiver.friends.add(application.sender)
    application.save()
    entity.save()

    if flag == 1:
        str = "已加好友"
    else:
        str = "拒绝加好友"
    return HttpResponse(str)


class UserPostView(ListView):
    """用户已发贴"""
    template_name = 'user_posts.html'
    context_object_name = 'user_posts'
    paginate_by = PAGE_NUM

    def get_queryset(self):
        user_posts = Post.objects.filter(author=self.request.user)
        return user_posts


class PostCreate(CreateView):
    """发帖"""
    model = Post
    template_name = 'form.html'
    form_class = PostForm
    # fields = ('title', 'column', 'type_name','content')
    # SAE django1.5中fields失效，不知原因,故使用form_class
    success_url = reverse_lazy('user_post')

    # 这里我们必须使用reverse_lazy() 而不是reverse，因为在该文件导入时URL 还没有加载。

    def form_valid(self, form):
        # 此处有待加强安全验证
        validate = self.request.POST.get('validate', None)
        formdata = form.cleaned_data
        if self.request.session.get('validate', None) != validate:
            return HttpResponse("验证码错误！<a href='/'>返回</a>")
        user = LoginUser.objects.get(username=self.request.user.username)
        # form.instance.author = user
        # form.instance.last_response  = user
        formdata['author'] = user
        formdata['last_response'] = user
        p = Post(**formdata)
        p.save()
        user.levels += 5  # 发帖一次积分加 5
        user.save()
        return HttpResponse("发贴成功！<a href='/'>返回</a>")


class PostUpdate(UpdateView):
    """编辑贴"""
    form_class = PostForm
    model = Post
    template_name = 'form.html'
    success_url = reverse_lazy('user_post')


class PostDelete(DeleteView):
    """删贴"""
    model = Post
    template_name = 'delete_confirm.html'
    success_url = reverse_lazy('user_post')


@login_required(login_url=reverse_lazy('user_login'))
def makecomment(request):
    """评论"""
    if request.method == 'POST':
        comment = request.POST.get("comment", "")
        post_id = request.POST.get("post_id", "")
        comment_id = request.POST.get("comment_id", "")

        user = LoginUser.objects.get(username=request.user)
        p = Post.objects.get(pk=post_id)
        p.responce_times += 1
        p.last_response = user

        if comment_id:
            p_comment = Comment.objects.get(pk=comment_id)
            c = Comment(
                post=p, author=user, comment_parent=p_comment, content=comment)
            c.save()
        else:
            c = Comment(post=p, author=user, content=comment)
            c.save()
        p.save()
        user.levels += 3  # 评论一次积分加 3
        user.save()

    return HttpResponse("评论成功")


class MessageCreate(CreateView):
    """发送消息"""
    model = Message
    template_name = 'form.html'
    form_class = MessageForm
    # fields = ('content',)
    # SAE django1.5中fields失效，不知原因,故使用form_class
    success_url = reverse_lazy('show_notice')

    def form_valid(self, form):
        # 此处有待加强安全验证
        sender = LoginUser.objects.get(username=self.request.user)
        receiver_id = int(self.kwargs.get('pk'))
        receiver = LoginUser.objects.get(id=receiver_id)
        formdata = form.cleaned_data
        formdata['sender'] = sender
        formdata['receiver'] = receiver
        m = Message(**formdata)
        m.save()
        return HttpResponse("消息发送成功！")


class MessageDetail(DetailView):
    """具体消息"""
    model = Message
    template_name = 'message.html'
    context_object_name = 'message'


def columnall(request):
    """所有板块"""
    column_list = Column.objects.all()
    return render(request, 'column_list.html', {'column_list': column_list})


def columndetail(request, column_pk):
    """每个板块"""
    column_obj = Column.objects.get(pk=column_pk)
    column_posts = column_obj.post_set.all()

    return render(request, 'column_detail.html', {
        'column_obj': column_obj,
        'column_posts': column_posts
    })

def likedetail(request):
    User_obj = LoginUser.objects.get(username=request.user)
    like_relations = User_obj.user_relations.all()
    like_posts = [like_relation.post for like_relation in like_relations]
    return render(request, 'user_likes.html', {
        'user_obj': User_obj,
        'like_posts': like_posts
    })

class SearchView(ListView):
    """搜索"""
    template_name = 'search_result.html'
    context_object_name = 'post_list'
    paginate_by = PAGE_NUM

    def get_context_data(self, **kwargs):
        kwargs['q'] = self.request.GET.get('srchtxt', '')
        return super(SearchView, self).get_context_data(**kwargs)

    def get_queryset(self):
        # 获取搜索的关键字
        q = self.request.GET.get('srchtxt', '')
        # 在帖子的标题和内容中搜索关键字
        post_list = Post.objects.only('title', 'content').filter(Q(title__icontains=q) | Q(content__icontains=q))
        return post_list


def validate(request):
    """验证码"""
    m_stream = BytesIO()
    validate_code = create_validate_code()
    img = validate_code[0]
    img.save(m_stream, "GIF")
    request.session['validate'] = validate_code[1]
    return HttpResponse(m_stream.getvalue(), "image/gif")


def upload_image(request):
    """编辑器图片上传"""
    if request.method == 'POST':
        callback = request.GET.get('CKEditorFuncNum')
        content = request.FILES["upload"]
        file_name = "static/upload_images/" + time.strftime("%Y%m%d%H%M%S", time.localtime()) + "_" + content.name
        file_path = os.path.join(settings.BASE_DIR, file_name)

        f = open(file_path, 'wb')
        for chunk in content.chunks():
            f.write(chunk)
        f.close()
        url = '/{}'.format(file_name)

        # try:
        #     body = content.read()
        #     # 存储到object storage
        #     file_path = os.path.join('static', 'upload', content.name)
        #
        #     url = ''
        #     from os import environ
        #     online = environ.get("APP_NAME", "")
        #
        #     if online:
        #         bucket = "mystorage"
        #         import sae.storage
        #         s = sae.storage.Client()
        #         ob = sae.storage.Object(content.read())
        #         url = s.put(bucket, file_name, ob)
        #
        #     else:
        #         url = None
        #
        # except Exception as e:
        #     url = str(e)

        url = '/' + url
        res = r"<script>window.parent.CKEDITOR.tools.callFunction(" + callback + ",'" + url + "', '');</script>"
        return HttpResponse(res)
    else:
        raise Http404()
