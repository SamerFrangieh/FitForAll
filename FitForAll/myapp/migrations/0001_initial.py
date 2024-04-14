# Generated by Django 4.2.11 on 2024-04-14 01:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Admin",
            fields=[
                ("admin_id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("password", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="Billing",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("amount_due", models.DecimalField(decimal_places=2, max_digits=10)),
                ("due_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("paid", "Paid"),
                            ("overdue", "Overdue"),
                        ],
                        max_length=20,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="EquipmentMaintenance",
            fields=[
                ("equipment_id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("last_maintenance_date", models.DateField()),
                ("next_maintenance_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("IN_MAINTENANCE", "In Maintenance"),
                            ("BROKEN", "Broken"),
                            ("FUNCTIONING", "Functioning"),
                        ],
                        default="FUNCTIONING",
                        max_length=15,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="GroupFitnessClass",
            fields=[
                (
                    "group_fitness_class_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("date", models.DateField()),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
            ],
        ),
        migrations.CreateModel(
            name="Member",
            fields=[
                ("member_id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("password", models.CharField(max_length=255)),
                ("health_metrics", models.JSONField()),
                (
                    "height",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                (
                    "weight",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                (
                    "goal_weight",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                ("weeks_to_goal", models.IntegerField(blank=True, null=True)),
                (
                    "diastolic_bp",
                    models.IntegerField(
                        default=0, null=True, verbose_name="Diastolic Blood Pressure"
                    ),
                ),
                (
                    "systolic_bp",
                    models.IntegerField(
                        default=0, null=True, verbose_name="Systolic Blood Pressure"
                    ),
                ),
                (
                    "fitness_goal",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="Fitness Goal",
                    ),
                ),
                (
                    "act_levels",
                    models.CharField(
                        blank=True,
                        default="1-3 x times a week",
                        max_length=255,
                        null=True,
                        verbose_name="Activity Levels",
                    ),
                ),
                (
                    "age",
                    models.DecimalField(
                        blank=True,
                        decimal_places=0,
                        default=20,
                        max_digits=3,
                        null=True,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Room",
            fields=[
                ("room_id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="Service",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("service_name", models.CharField(max_length=255)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name="Trainer",
            fields=[
                ("trainer_id", models.AutoField(primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("password", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="TrainerAvailability",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "day_of_week",
                    models.IntegerField(
                        choices=[
                            (0, "Sunday"),
                            (1, "Monday"),
                            (2, "Tuesday"),
                            (3, "Wednesday"),
                            (4, "Thursday"),
                            (5, "Friday"),
                            (6, "Saturday"),
                        ]
                    ),
                ),
                ("check_in", models.TimeField()),
                ("check_out", models.TimeField()),
                (
                    "trainer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="availabilities",
                        to="myapp.trainer",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RoomBooking",
            fields=[
                (
                    "room_booking_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                (
                    "room",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bookings",
                        to="myapp.room",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PersonalSession",
            fields=[
                (
                    "personal_session_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("date", models.DateField()),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="personal_sessions",
                        to="myapp.member",
                    ),
                ),
                (
                    "trainer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="personal_sessions",
                        to="myapp.trainer",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("payment_date", models.DateField()),
                ("payment_method", models.CharField(max_length=50)),
                (
                    "payment_status",
                    models.CharField(
                        choices=[("successful", "Successful"), ("failed", "Failed")],
                        max_length=20,
                    ),
                ),
                (
                    "billing",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="myapp.billing",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MemberGroupFitnessRegistration",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("registration_date", models.DateField(auto_now_add=True)),
                (
                    "group_fitness_class",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="registrations",
                        to="myapp.groupfitnessclass",
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="group_fitness_registrations",
                        to="myapp.member",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="groupfitnessclass",
            name="room",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="group_fitness_classes",
                to="myapp.room",
            ),
        ),
        migrations.AddField(
            model_name="groupfitnessclass",
            name="trainer",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="group_fitness_classes",
                to="myapp.trainer",
            ),
        ),
        migrations.AddField(
            model_name="billing",
            name="member",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="billings",
                to="myapp.member",
            ),
        ),
    ]
