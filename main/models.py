from django.db import models
from django.conf import settings
from ckeditor.fields import RichTextField


class Company(models.Model):
    name = models.CharField(max_length=30)
    description = RichTextField(max_length=200, default=None)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='owner')
    employees = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='employees')
    logo = models.ImageField(default=None, blank=True, null=True, upload_to='media/')

    def __str__(self):
        return self.name


class Project(models.Model):

    WAITING = "Beklemede"
    INACTIVE = "İnaktif"
    ACTIVE = "Aktif"
    DONE = "Tamamlandı"

    STATUS_CHOICES = (
        (WAITING, "Beklemede"),
        (INACTIVE, "İnaktif"),
        (ACTIVE, "Aktif"),
        (DONE, "Tamamlandı"),
    )

    name = models.CharField(max_length=30, default=None)
    description = RichTextField(max_length=1000, default=None)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                              blank=True, on_delete=models.SET_NULL, related_name='project_owner')
    company = models.ForeignKey(Company, null=True, blank=True, on_delete=models.SET_NULL)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='users')
    date_created = models.DateField(auto_now_add=True)
    is_private = models.BooleanField(default=False, blank=True)
    status = models.CharField(max_length=11, choices=STATUS_CHOICES, default=ACTIVE, blank=True)


class PinnedProjects(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=False, default=None)
    pinned_at = models.DateTimeField(auto_now_add=True, blank=True)


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

    WAITING = "Beklemede"
    INACTIVE = "İnaktif"
    ACTIVE = "Aktif"
    DONE = "Tamamlandı"

    STATUS_CHOICES = (
        (WAITING, "Beklemede"),
        (INACTIVE, "İnaktif"),
        (ACTIVE, "Aktif"),
        (DONE, "Tamamlandı"),
    )

    title = models.CharField(max_length=30)
    description = models.CharField(max_length=300)
    assigned_to = models.ManyToManyField(settings.AUTH_USER_MODEL)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, blank=True)
    priority = models.CharField(max_length=6, choices=PRIORITY_CHOICES, default=MID)
    status = models.CharField(max_length=11, choices=STATUS_CHOICES, default=WAITING)


class Post(models.Model):
    title = models.CharField(max_length=30)
    content = RichTextField(max_length=500)
    files = models.FileField(upload_to='uploads/', null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    board = models.ForeignKey(Board, null=True, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, null=True, on_delete=models.CASCADE)
    date_created = models.DateField(auto_now_add=True)


class Label(models.Model):
    title = models.CharField(max_length=30)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, blank=True, on_delete=models.CASCADE)
    tagged_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='tagged_users')
    tagged_tasks = models.ManyToManyField(Task, blank=True)
    tagged_boards = models.ManyToManyField(Board, blank=True)


class Message(models.Model):
    title = models.CharField(max_length=30)
    content = RichTextField(max_length=200)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    # recipients = models.ManyToManyField(settings.AUTH_USER_MODEL)  //??


class ProjectStaff(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=False, default=None)


class Invitation(models.Model):
    inviter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sender')
    invited = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recipient')
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    date_created = models.DateField(auto_now_add=True)
