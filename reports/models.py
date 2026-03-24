from django.db import models


class DailyPlacementSnapshot(models.Model):
    report_date = models.DateField(db_index=True)
    branch_code = models.PositiveIntegerField()
    branch_name = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("report_date", "branch_code")
        ordering = ("-report_date", "branch_code")

    def __str__(self) -> str:
        return f"{self.report_date} | {self.branch_code} | {self.amount}"
