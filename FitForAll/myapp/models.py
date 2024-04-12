from django.db import models
from django.contrib.postgres.fields import JSONField


class Member(models.Model):
    member_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    password = models.CharField(max_length=255)  # Consider using Django's built-in User model for better security
    health_metrics = models.JSONField()
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Allow null if optional
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Allow null if optional
    goal_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weeks_to_goal = models.IntegerField(null=True, blank=True)
    diastolic_bp = models.IntegerField(verbose_name="Diastolic Blood Pressure", default=0)
    systolic_bp = models.IntegerField(verbose_name="Systolic Blood Pressure", default=0)
    fitness_goal = models.CharField(max_length=255, blank=True, verbose_name="Fitness Goal")
    act_levels = models.CharField(max_length=255, blank=True, verbose_name="Activity Levels")

class Trainer(models.Model):
    trainer_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    password = models.CharField(max_length=255) 


class TrainerAvailability(models.Model):
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=[
        (0, 'Sunday'),
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
    ])
    check_in = models.TimeField()
    check_out = models.TimeField()

    def __str__(self):
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        return f"{self.trainer.name} - {days[self.day_of_week]}"
class Admin(models.Model):
    admin_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    password = models.CharField(max_length=255) 

class FitnessClass(models.Model):
    class_id = models.AutoField(primary_key=True)
    class_name = models.CharField(max_length=255)
    room_id = models.IntegerField()
    schedule = models.DateTimeField()

class RoomBooking(models.Model):
    booking_id = models.AutoField(primary_key=True)
    room_id = models.IntegerField()
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

class EquipmentMaintenance(models.Model):
    equipment_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    last_maintenance_date = models.DateField()
    next_maintenance_date = models.DateField()

class Billing(models.Model):
    bill_id = models.AutoField(primary_key=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    payment_date = models.DateField(blank=True, null=True)

