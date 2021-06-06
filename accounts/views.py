from django.views.generic import CreateView
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.contrib import messages
from accounts.forms import UserRegistrationForm, LoginForm

class UserRegistrationView(CreateView):
    model = get_user_model()
    form_class = UserRegistrationForm
    success_url = '/worklist/index'

class UserLoginView(LoginView):
    authentication_form = LoginForm
    template_name = 'accounts/login_form.html'

    def form_invalid(self, form):
        messages.error(self.request, 'Login Failed', extra_tags='danger')
        return super().form_invalid(form)


