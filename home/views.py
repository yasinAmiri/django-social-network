from django.db.models import Model
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .models import Post, Comment, Vote
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .forms import PostCreateUpdateForm, CommentCreateForm, CommentReplyForm, PostSearchForm
from django.utils.text import slugify
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, RedirectView, CreateView, UpdateView, MonthArchiveView
from django.urls import reverse_lazy




class MonthPostsView(MonthArchiveView):
    model = Post
    date_field = "created"
    template_name = "home/index.html"
    context_object_name = "posts"



class HomeView(View):
    form_class = PostSearchForm
    http_method_names = ['get', 'options']

    def get(self, request):
        posts = Post.objects.all()
        if request.GET.get("search", None):
            posts = posts.filter(body__icontains=request.GET['search'])

        return render(request, 'home/index.html', {'posts':posts, 'form':self.form_class})

    def options(self, request, *args, **kwargs):
        response = super().options(request, *args, **kwargs)
        response.headers['host'] = 'localhost'
        response.headers['user'] = request.user
        return response

    def http_method_not_allowed(self, request, *args, **kwargs):
        super().http_method_not_allowed(request, *args, **kwargs)
        return render(request, 'method_not_allowed.html')



class PostDetailView(View):
    form_class       = CommentCreateForm
    form_class_reply = CommentReplyForm


    def setup(self, request, *args, **kwargs):
        self.post_instance = get_object_or_404(Post, id=kwargs['post_id'], slug=kwargs['post_slug'])
        return super().setup(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        comments = self.post_instance.pcomments.filter(is_reply=False)
        can_like = False
        if request.user.is_authenticated and self.post_instance.user_can_like(request.user):
            can_like = True
        return render(request, "home/detail.html", {'post':self.post_instance,
                                                                       'comments':comments,
                                                                       'form':self.form_class,
                                                                       'reply_form':self.form_class_reply,
                                                                       'can_like':can_like})

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            new_comment      = form.save(commit=False)
            new_comment.user = request.user
            new_comment.post = self.post_instance
            new_comment.save()
            messages.success(request, "Comment saved successfully", "success")
            return redirect("home:post_detail", self.post_instance.id, self.post_instance.slug)



class PostDeleteView(LoginRequiredMixin, View):
    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        if post.user.id == request.user.id:
            post.delete()
            messages.success(request, 'post deleted successfully', 'success')
        else:
            messages.error(request, 'you cannot delete this post', 'danger')
        return redirect('home:home')



class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    fields = ['body']
    success_url = reverse_lazy("home:home")

    def form_valid(self, form):
        if self.object.user.id != self.request.user.id:
            messages.error(self.request, "You cannot update this post", "danger")
            return redirect("home:home")
        return super().form_valid(form)



class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['body']
    template_name = "home/create.html"
    success_url = reverse_lazy("home:home")

    def form_valid(self, form):
        self._create_post(form)
        return super().form_valid(form)

    def _create_post(self, form):
        post = form.save(commit=False)
        post.slug = slugify(form.cleaned_data['body'][:30])
        post.user = self.request.user
        post.save()
        messages.success(self.request, "post created successfully", "success")



class PostAddReplyView(LoginRequiredMixin, View):
    form_class = CommentReplyForm

    def post(self, request, post_id, comment_id):
        post    = get_object_or_404(Post, id=post_id)
        comment = get_object_or_404(Comment, id=comment_id)
        form    = self.form_class(request.POST)
        if form.is_valid():
            reply          = form.save(commit=False)
            reply.user     = request.user
            reply.post     = post
            reply.reply    = comment
            reply.is_reply = True
            reply.save()
            messages.success(request, 'reply submitted successfully', 'success')
        return redirect('home:post_detail', post.id, post.slug)



class PostLikeView(LoginRequiredMixin, View):
    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        like = Vote.objects.filter(post=post, user=request.user)
        if like.exists():
            messages.error(request, "You have already liked this post", "warning")
        else:
            Vote.objects.create(post=post, user=request.user)
            messages.success(request, "You liked this post", "success")
        return redirect("home:post_detail", post.id, post.slug)



class AboutView(TemplateView):
    template_name = "home/about.html"
    
    def get_context_data(self, **kwargs):
        context         = super().get_context_data(**kwargs)
        context['user'] = self.request.user.username
        return context



class ContactView(RedirectView):
    url          = '/about/%(id)i/%(name)s/'
    permanent    = True
    query_string = False

    def get_redirect_url(self, *args, **kwargs):
        print('='*90)
        print(kwargs['id'], kwargs['name'])
        return super().get_redirect_url(*args, **kwargs)












