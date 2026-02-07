from django.contrib.auth import authenticate, login, get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
import json
from .models import Member, Course, Lecture


def members(request):
    mymembers = Member.objects.all().values()
    template = loader.get_template('mainpage.html')
    context = {
        'mymembers': mymembers,
    }
    return HttpResponse(template.render(context, request))


def login_view(request):
    message = ""
    next_url = request.GET.get("next") or request.POST.get("next") or "profile"
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not email or not password:
            message = "Please enter both email and password."
        else:
            try:
                validate_email(email)
            except ValidationError:
                message = "Please enter a valid email address."
            else:
                # 1. Try to authenticate as existing user (username = email)
                user = authenticate(request, username=email, password=password)

                if user is not None:
                    login(request, user)
                    return redirect(next_url)

                # 2. If user does not exist — create new account (registration)
                User = get_user_model()
                existing = User.objects.filter(username=email).first()

                if existing is not None:
                    message = "Invalid email or password."
                else:
                    user = User.objects.create_user(username=email, email=email, password=password)
                    Member.objects.create(
                        user=user,
                        first_name=email.split("@")[0],
                        last_name="",
                        phone=None,
                        joined_date=None,
                    )
                    login(request, user)
                    return redirect(next_url)

    return render(request, "login.html", {"message": message, "next": next_url})


def courses_view(request):
    courses = [
        {"id": c.slug, "title": c.title, "description": c.description}
        for c in Course.objects.all()
    ]
    return render(request, "courses.html", {"courses": courses})


def course_lectures_view(request, course_id: str):
    try:
        course = Course.objects.get(slug=course_id)
    except Course.DoesNotExist:
        return render(
            request,
            "lectures.html",
            {
                "course_id": course_id,
                "course_title": "Course",
                "lectures": [],
                "active_lecture": None,
                "message": "Course not found.",
                "progress_percent": 0,
            },
        )

    lectures = list(course.lectures.all())
    if not lectures:
        return render(
            request,
            "lectures.html",
            {
                "course_id": course_id,
                "course_title": course.title,
                "lectures": [],
                "active_lecture": None,
                "message": "Lectures for this course are coming soon.",
                "progress_percent": 0,
            },
        )

    active_id = request.GET.get("lecture")
    if active_id:
        try:
            active_lecture = course.lectures.get(pk=active_id)
        except (Lecture.DoesNotExist, ValueError):
            active_lecture = lectures[0]
    else:
        active_lecture = lectures[0]

    completed_count = 0
    progress_percent = int((completed_count / max(len(lectures), 1)) * 100)

    return render(
        request,
        "lectures.html",
        {
            "course_id": course_id,
            "course_title": course.title,
            "lectures": lectures,
            "active_lecture": active_lecture,
            "message": "",
            "progress_percent": progress_percent,
        },
    )


def profile_view(request):
    """
    Simple user profile page that mirrors the layout from the mockup
    but with a cleaner, more modern visual style.
    Requires authentication: redirects to login if user came from main/courses without registering.
    """
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={reverse('profile')}")

    user = request.user
    member = None
    if user.is_authenticated:
        try:
            member = Member.objects.get(user=user)
        except Member.DoesNotExist:
            member = None
        
        if member:
            display_name = f"{member.first_name} {member.last_name}".strip() or user.get_username() or "User"
        else:
            display_name = user.get_full_name() or user.get_username() or "User"
        user_id = f"id:{user.id:06d}"
    else:
        display_name = "Guest"
        user_id = "id:000000"

    # Placeholder data – can later be replaced with real progress
    xp_percent = 62
    achievements = [
        {
            "title": "First Steps",
            "subtitle": "Completed your first lecture",
            "icon": "pulse",
        },
        {
            "title": "Risk Watcher",
            "subtitle": "Reviewed basic cyber risks",
            "icon": "alert",
        },
    ]

    return render(
        request,
        "profile.html",
        {
            "display_name": display_name,
            "user_id": user_id,
            "xp_percent": xp_percent,
            "achievements": achievements,
            "member": member,
            "user": user,
        },
    )


@require_http_methods(["POST"])
@ensure_csrf_cookie
def update_profile_view(request):
    """
    Update user profile (first_name, last_name, email)
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Not authenticated"}, status=401)
    
    try:
        data = json.loads(request.body)
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        email = data.get("email", "").strip()
        
        # Get or create Member for this user
        member, created = Member.objects.get_or_create(
            user=request.user,
            defaults={
                "first_name": first_name or request.user.username,
                "last_name": last_name,
                "email": email or request.user.email,
            }
        )
        
        # Update fields
        if first_name:
            member.first_name = first_name
        if last_name:
            member.last_name = last_name
        if email:
            member.email = email
            # Also update User email if needed
            request.user.email = email
            request.user.save()
        
        member.save()
        
        return JsonResponse({
            "success": True,
            "message": "Profile updated successfully",
            "data": {
                "first_name": member.first_name,
                "last_name": member.last_name,
                "email": member.email or request.user.email,
            }
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


def settings_view(request):
    """
    Simple settings page that uses the standalone settings.html
    template. Behaviour is a static prototype for now.
    """
    return render(request, "settings.html")
