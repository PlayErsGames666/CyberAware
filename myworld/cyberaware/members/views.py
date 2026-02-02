from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.template import loader
from .models import Member


def members(request):
    mymembers = Member.objects.all().values()
    template = loader.get_template('mainpage.html')
    context = {
        'mymembers': mymembers,
    }
    return HttpResponse(template.render(context, request))


def login_view(request):
    message = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("members")
        else:
            message = "Invalid login or password."

    return render(request, "login.html", {"message": message})


def courses_view(request):
    courses = [
        {
            "id": "cti",
            "title": "Cyber Threat Intelligence",
            "description": (
                "Learn how to collect, analyze, and use threat intelligence to predict attacks, "
                "prioritize risks, and make better security decisions."
            ),
        },
        {
            "id": "df",
            "title": "Digital Forensics",
            "description": (
                "Understand how to preserve evidence, investigate incidents, and reconstruct what "
                "happened using logs, disk artifacts, and memory analysis."
            ),
        },
        {
            "id": "wh",
            "title": "White Hacker",
            "description": (
                "Practice ethical hacking foundations: reconnaissance, common vulnerabilities, "
                "and safe exploitation methods to improve defenses."
            ),
        },
        {
            "id": "aics",
            "title": "AI Cyber Security",
            "description": (
                "Explore how AI is used in security: anomaly detection, phishing detection, "
                "SOC automation, and the risks of adversarial ML."
            ),
        },
    ]
    return render(request, "courses.html", {"courses": courses})


def course_lectures_view(request, course_id: str):
    course_titles = {
        "cti": "Cyber Threat Intelligence",
        "df": "Digital Forensics",
        "wh": "White Hacker",
        "aics": "AI Cyber Security",
    }

    if course_id != "cti":
        return render(
            request,
            "lectures.html",
            {
                "course_id": course_id,
                "course_title": course_titles.get(course_id, "Course"),
                "lectures": [],
                "active_lecture": None,
                "message": "Lectures for this course are coming soon.",
                "progress_percent": 0,
            },
        )

    lectures = [
        {
            "id": "l1",
            "title": "Lecture 1",
            "heading": "Lecture Number 1",
            "content": "Threat intelligence basics: sources, types (strategic/operational/tactical), and the intel lifecycle.",
        },
        {
            "id": "l2",
            "title": "Lecture 2",
            "heading": "Lecture Number 2",
            "content": "IOC vs IOA, ATT&CK mapping, and how to turn raw indicators into actionable detections.",
        },
        {
            "id": "l3",
            "title": "Lecture 3",
            "heading": "Lecture Number 3",
            "content": "Threat actor profiling, TTPs, reporting structure, and communicating risk to stakeholders.",
        },
        {
            "id": "l4",
            "title": "Lecture 4",
            "heading": "Lecture Number 4",
            "content": "Collection & automation: feeds, enrichment, scoring, and basic TI workflows for a SOC.",
        },
    ]

    active_id = request.GET.get("lecture") or lectures[0]["id"]
    active_lecture = next((l for l in lectures if l["id"] == active_id), lectures[0])

    completed_count = 0
    progress_percent = int((completed_count / max(len(lectures), 1)) * 100)

    return render(
        request,
        "lectures.html",
        {
            "course_id": course_id,
            "course_title": course_titles[course_id],
            "lectures": lectures,
            "active_lecture": active_lecture,
            "message": "",
            "progress_percent": progress_percent,
        },
    )
