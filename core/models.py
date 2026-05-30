from django.db import models


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

    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name="scans")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    scores = models.JSONField(default=dict)
    gate = models.CharField(max_length=10, default="")
    full_mode = models.BooleanField(default=False)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["repository", "started_at"]),
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
