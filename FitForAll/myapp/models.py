from django.db import models
from django.contrib.postgres.fields import JSONField

class Member(models.Model):
    member_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    fitness_goal = models.CharField(max_length=255, blank=True)
    health_metrics = models.JSONField()

class Trainer(models.Model):
    trainer_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    availability = models.JSONField()

class AdminStaff(models.Model):
    staff_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

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
