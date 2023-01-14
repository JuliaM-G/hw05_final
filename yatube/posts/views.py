from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import pages


@cache_page(20, key_prefix='index_page')
def index(request):
    template_name = 'posts/index.html'
    post_list = Post.objects.all()
    context = pages(post_list, request)
    return render(request, template_name, context)


def group_posts(request, slug):
    template_name = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        'group': group,
        'posts': posts,
    }
    context.update(pages(posts, request))
    return render(request, template_name, context)


def profile(request, username):
    template_name = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts_number = author.posts.all().count()
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author
    ).exists()
    context = {
        'author': author,
        'posts_number': posts_number,
        'following': following,
    }
    context.update(pages(author.posts.all(), request))
    return render(request, template_name, context)


def post_detail(request, post_id):
    template_name = 'posts/post_detail.html'
    one_post = get_object_or_404(Post, id=post_id)
    posts_number = one_post.author.posts.all().count()
    form = CommentForm(request.POST or None)
    comments = one_post.comments.all()
    context = {
        'one_post': one_post,
        'posts_number': posts_number,
        'form': form,
        'comments': comments,
    }
    return render(request, template_name, context)


@login_required
def post_create(request):
    template_name = 'posts/create_post.html'
    form = PostForm(request.POST or None)
    context = {
        'form': form,
    }
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', username=new_post.author)
    form = PostForm()
    context = {
        'form': form,
    }
    return render(request, template_name, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True,
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template_name = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    context = pages(posts, request)
    return render(request, template_name, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:follow_index')
