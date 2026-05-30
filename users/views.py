from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from rides.models import Ride
from users.forms import ProfileForm, UserLoginForm, UserPasswordChangeForm, UserRegistrationForm


def register(request):
    # После успешной регистрации сразу авторизуем пользователя.
    if request.method == "POST":
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Регистрация прошла успешно.")
            return redirect("rides:index")
        messages.error(request, "Проверьте форму регистрации.")
    else:
        form = UserRegistrationForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("rides:index")
    form = UserLoginForm(request, data=request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            login(request, form.get_user())
            messages.success(request, "Вы вошли в аккаунт.")
            return redirect("rides:index")
        messages.error(request, "Неверный логин или пароль.")
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "Вы вышли из аккаунта.")
    return redirect("rides:index")


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль обновлен.")
            return redirect("users:profile")
        messages.error(request, "Не удалось сохранить профиль.")
    else:
        form = ProfileForm(instance=request.user)

    recent_rides = Ride.objects.filter(user=request.user).select_related("tariff").order_by("-created_at")[:5]
    return render(
        request,
        "users/profile.html",
        {
            "form": form,
            "recent_rides": recent_rides,
        },
    )


@login_required
def security(request):
    if request.method == "POST":
        form = UserPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Пароль успешно обновлён.")
            return redirect("users:security")
        messages.error(request, "Не удалось поменять пароль. Проверьте форму.")
    else:
        form = UserPasswordChangeForm(user=request.user)

    return render(request, "users/security.html", {"form": form})
