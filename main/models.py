from django.db import models
from django.conf import settings
from ckeditor.fields import RichTextField


class Company(models.Model):
    name = models.CharField(max_length=30)
    description = RichTextField(max_length=200, default=None)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    employees = models.ManyToManyField(settings.AUTH_USER_MODEL, null=True, blank=True)


class Project(models.Model):
    name = models.CharField(max_length=30, default=None)
    description = RichTextField(max_length=200, default=None)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, on_delete=models.SET_NULL)
    company = models.ForeignKey(Company, null=True, blank=True, on_delete=models.SET_NULL)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, null=True, blank=True)
    date_created = models.DateField(auto_now_add=True)


class Board(models.Model):
    title = models.CharField(null=True, max_length=30)
    description = models.TextField(null=True, max_length=200)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    is_pinned = models.BooleanField(default=False, blank=True)


class Task(models.Model):

    LOW = "Düşük"
    MID = "Orta"
    HIGH = "Yüksek"

    PRIORITY_CHOICES = (
        (LOW, "Düşük"),
        (MID, "Orta"),
        (HIGH, "Yüksek"),
    )

    title = models.CharField(max_length=30)
    description = models.CharField(max_length=300)
    assigned_to = models.ManyToManyField(settings.AUTH_USER_MODEL)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, blank=True)
    priority = models.CharField(max_length=5, choices=PRIORITY_CHOICES, default=MID)


class Post(models.Model):
    title = models.CharField(max_length=30)
    content = RichTextField(max_length=500)
    files = models.FileField(upload_to='uploads/', null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    board = models.ForeignKey(Board, null=True, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, null=True, on_delete=models.CASCADE)
    date_created = models.DateField(auto_now_add=True)


class Label(models.Model):
    title = models.CharField(max_length=30)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, blank=True, on_delete=models.CASCADE)
    tagged_users = models.ManyToManyField(settings.AUTH_USER_MODEL, null=True, blank=True)
    tagged_tasks = models.ManyToManyField(Task, null=True, blank=True)
    tagged_boards = models.ManyToManyField(Board, null=True, blank=True)


class Message(models.Model):
    title = models.CharField(max_length=30)
    content = RichTextField(max_length=200)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    # recipients = models.ManyToManyField(settings.AUTH_USER_MODEL)  //??
