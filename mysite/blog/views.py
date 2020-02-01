from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm
from taggit.models import Tag


def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 1)  # means 1 articles for each page
    page = request.GET.get('page')

    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(int(page // 1))
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(request, 'blog/post/list.html', {'page': page,
                                                   'posts': posts,
                                                   'tag': tag})


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    if request.method:
        form = EmailPostForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = '{} ({}) recommends you reading "' \
                      '{}"'.format(cd['name'], cd['email'], post.title)
            message = 'Read "{}" at {}\n\n{}\'s comments: ' \
                      '{}'.format(post.title, post_url, cd['name'], cd['comments'])
            send_mail(subject, message, 'admin@myblog', [cd['to']])
            sent = True

            return render(request, 'blog/post/share.html',
                          {'post': post, 'form': form, 'sent': sent})

        else:
            form = EmailPostForm()
            return render(request, 'blog/post/share.html',
                          {'post': post, 'form': form, 'sent': sent})


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 2
    template_name = 'blog/post/list.html'


def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post, slug=post, status='published',
        publish__year=year,
        publish__month=month, publish__day=day
    )
    comments = post.comments.filter(active=True)
    new_comment = None
    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = post
            new_comment.save()
            return HttpResponseRedirect(request.path)
            # Предотвращение повторной отправки формы
        else:
            comment_form = CommentForm()
    else:
        comment_form = None  # затычка

    return render(request, 'blog/post/detail.html',
                  {'post': post,
                   'comments': comments,
                   'new_comment': new_comment,
                   'comment_form': comment_form})
