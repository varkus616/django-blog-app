from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Post, Message
from django.http import Http404
from .forms import PostForm, SendMessageForm, ProfileForm
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic.edit import CreateView
from django.contrib.auth.views import LoginView


class MyLoginView(LoginView):
    template_name = 'blog/registration/login.html'
    authentication_form = AuthenticationForm

    def form_valid(self, form):
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect to the user's profile page
        return reverse_lazy('blog:profile', kwargs={'username': self.request.user.username})


class MyRegistrationView(CreateView):
    template_name = 'blog/registration/register.html'
    form_class = UserCreationForm
    profile_form_class = ProfileForm  # Add the ProfileForm
    success_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile_form'] = self.profile_form_class()  # Add the profile form to context
        return context

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        profile_form = self.profile_form_class(request.POST)
        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            login(request, user)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

@login_required
def user_logout(request):
    logout(request)
    return redirect('blog:login')


@login_required
def delete_user(request):
    if request.method == 'POST':
        user = request.user
        user.delete()
        return redirect('login')
    return render(request, 'registration/delete.html')


def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})


class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    fields = ['title', 'content', 'author']
    template_name = 'blog/post_detail.html'
    success_url = reverse_lazy('blog:post_list')

    def get_queryset(self):
        return Post.objects.filter(pk=self.kwargs['pk'])


def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.publish()
            return redirect('blog:post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})


def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.published_date = timezone.now()
            post.save()
            return redirect('blog:post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form': form})


@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if post.author != request.user:
        return HttpResponseForbidden()

    if request.method == "POST":
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    else:
        print("tutaj!")
        return render(request, 'blog/registration/profile.html', {'post': post})


class UsersListView(ListView):
    model = User
    template_name = 'blog/registration/users.html'
    context_object_name = 'users_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        logged_in_user = self.request.user

        excluded_users = User.objects.filter(~Q(id=logged_in_user.id) & ~Q(is_superuser=True))

        context['users_list'] = excluded_users

        return context


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'blog/registration/profile.html'
    context_object_name = 'viewed_user'
    pk_url_kwarg = 'pk'

    def get_object(self, queryset=None):
        username = self.kwargs.get('username')
        return User.objects.get(username=username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        viewed_user = self.get_object()
        # Check if the user is authenticated
        if self.request.user.is_authenticated:
            # If the viewed user is the logged-in user
            user_profile = viewed_user.userprofile
            friends = user_profile.friends.all()
            posts = Post.objects.filter(author=self.request.user)

            context['user_posts'] = posts
            context['user_friends'] = friends
            if viewed_user == self.request.user:

                context['logged_profile'] = True
            else:

                context['logged_profile'] = False
        else:
            context['message'] = "Please log in to view full profile."

        return context

    def dispatch(self, request, *args, **kwargs):
        """
        Override the dispatch method to handle admin redirection.
        """
        viewed_user = self.get_object()
        # Check if the viewed user is an admin
        if viewed_user.is_superuser:
            # Redirect to a specific page if the viewed user is an admin
            return redirect('blog:post_list')

        return super().dispatch(request, *args, **kwargs)


@login_required
def remove_friend(request, username):
    try:
        friend = User.objects.get(username=username)
        friend_profile = friend.userprofile
        user_profile = request.user.userprofile
    except User.DoesNotExist:
        raise Http404("User does not exist")

    if friend_profile is None or user_profile is None:
        raise Http404("User profile does not exist")

    if friend_profile not in user_profile.friends.all() or user_profile not in friend_profile.friends.all():
        raise Http404("Friend not found in user's friend list")

    friend_profile.friends.remove(user_profile)
    user_profile.friends.remove(friend_profile)

    return redirect('blog:profile', username=request.user.username)


class InboxView(ListView):
    template_name = 'blog/registration/inbox.html'
    context_object_name = 'messages'

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(to_user=user)


@login_required
def accept_invitation(request, username):
    from_user = get_object_or_404(User,username=username)
    to_user = request.user

    if not from_user.userprofile.friends.filter(user=to_user).exists() and \
           not to_user.userprofile.friends.filter(user=from_user).exists():

       from_user.userprofile.friends.add(to_user.userprofile)
       to_user.userprofile.friends.add(from_user.userprofile)

    return redirect('blog:inbox', username=request.user.username)


@login_required
def delete_msg(request, msg_pk):
    msg = get_object_or_404(Message, id=msg_pk)

    msg.delete()

    return redirect('blog:inbox', username=request.user.username)


@login_required
def send_friend_invitation(request, username):
    msg = None
    if request.method == 'POST':
        current_user = request.user
        other_user = get_object_or_404(User, username=username)
        if current_user != other_user:
            if not current_user.userprofile.friends.filter(pk=other_user.pk).exists() and \
               not other_user.userprofile.friends.filter(pk=current_user.pk).exists():
                metadata = {"from_user":current_user,
                            "to_user":other_user}
                html_content = render_to_string('blog/registration/invitation_msg.html',
                                                {'meta_data': metadata})

                invitation = Message(
                    from_user=current_user,
                    to_user=other_user,
                    body=html_content,
                    seen=False,
                    subject="Someone sent you invitation!"
                )
                invitation.send()

                msg = "Friend request send!"
            else:
                msg = "You are already friends!"
        else:
            msg = "You cannot add yourself as a friend!"

    return render(request, 'blog/registration/friend_added_sucessfully.html',
                  {
                      "msg": msg
                  })


def send_message(request, username):
    messages = []
    to_user = get_object_or_404(User, username=username)
    from_user = request.user

    msg = Message(
        to_user=to_user,
        from_user=from_user)

    if request.method == "POST":
        form = SendMessageForm(request.POST, instance=msg)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.send()
            return redirect('blog:profile', from_user.username)
        else:
            messages.append("An error occurred while processing the form. "
                            "Please check the entered data and try again.")
            return render(request, "blog/registration/send_message.html",
                          {"messages": messages, "form": form})
    else:
        form = SendMessageForm()
    return render(request, "blog/registration/send_message.html",
                  {"messages": messages, "form": form})

