from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DailyPlacementSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("report_date", models.DateField(db_index=True)),
                ("branch_code", models.PositiveIntegerField()),
                ("branch_name", models.CharField(max_length=120)),
                ("amount", models.DecimalField(decimal_places=2, default=0, max_digits=18)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ("-report_date", "branch_code"),
                "unique_together": {("report_date", "branch_code")},
            },
        ),
    ]
