from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Extended user profile for scan quotas and billing."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    scans_used = models.PositiveIntegerField(default=0)
    scans_limit = models.PositiveIntegerField(default=50)  # 50 free audits
    paid = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    figma_token = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def scans_remaining(self):
        return max(0, self.scans_limit - self.scans_used)

    @property
    def can_scan(self):
        return self.scans_remaining > 0 or self.paid

    def __str__(self):
        return f"{self.user.email} — {self.scans_used}/{self.scans_limit} scans"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


class Repository(models.Model):
    """Represents a repository being scanned for viability."""
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=1024, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "repositories"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class ScanRun(models.Model):
    """Records a single viability scan execution."""
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scans", null=True, blank=True)
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name="scans", null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    scores = models.JSONField(default=dict)
    gate = models.CharField(max_length=10, default="")
    full_mode = models.BooleanField(default=False)
    report_url = models.URLField(blank=True)
    figma_url = models.URLField(blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["user", "started_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.repository.name} @ {self.started_at}"


class Finding(models.Model):
    """Individual finding from a scan layer."""
    class Severity(models.TextChoices):
        CRITICAL = "CRITICAL", "Critical"
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"
        INFO = "INFO", "Info"

    scan = models.ForeignKey(ScanRun, on_delete=models.CASCADE, related_name="findings")
    layer = models.CharField(max_length=50)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    title = models.CharField(max_length=500)
    file = models.CharField(max_length=1024, blank=True)
    line = models.PositiveIntegerField(null=True, blank=True)
    remediation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["scan", "severity"]),
            models.Index(fields=["layer"]),
        ]

    def __str__(self):
        return f"[{self.severity}] {self.title}"
