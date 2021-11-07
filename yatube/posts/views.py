from django.shortcuts import redirect, render, get_object_or_404
from .models import Post, Group, User, Follow
from django.core.paginator import Paginator
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    template = 'posts/group_list.html'
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)

    post_list = author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    num = post_list.count()
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=author).exists()
    else:
        following = False
    context = {
        "page_obj": page_obj,
        "num": num,
        "author": author,
        "following": following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all
    form = CommentForm(request.POST or None)
    author_all_posts = post.author.posts.all()
    num_of_posts = author_all_posts.count()
    text = post.text[:30]
    context = {
        "post": post,
        "text": text,
        "num": num_of_posts,
        "comments": comments,
        "form": form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    username = request.user.username
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid() and request.method == 'POST':
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=username)
    return render(request, 'posts/post_create.html',
                           {'form': form, 'is_edit': False})


def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/post_create.html',
                           {'form': form, 'is_edit': True,
                            'post_id': post_id})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid() and request.method == "POST":
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follow_list = request.user.following.all()
    author_list = []
    for follow in follow_list:
        author_list.append(follow.author)
    post_list = Post.objects.filter(author__in=author_list)
    paginator = Paginator(post_list, 10)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    test_exist = Follow.objects.filter(user=request.user,
                                       author=author).exists()
    if author != request.user and not test_exist:
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User, username=username)
    if author != request.user:
        follow = get_object_or_404(Follow, user=request.user, author=author)
        follow.delete()
    return redirect('posts:profile', username=username)
