from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Member
from django.db import connection
 # Prints the last executed query
# #from .models import Book
# def member_login(request):
#     return render(request, 'myapp/login/memberLogin.html')

def dashboard_view(request):
    # Will put objects here once Samer creates dashboard frontend
    # objects = YourModel.objects.all()

    # Dashboard no context
    return render(request, 'myapp/dashboard/index.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Member

def register(request):
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        password = request.POST.get('password').strip()
        fitness_goals = request.POST.get('goals', '').strip() # Optional, provide default
        height = request.POST.get('height').strip()
        weight = request.POST.get('weight').strip()

        # Basic validation (you might want to add more, e.g., checking if user already exists)
        if not (name and password and height and weight):
            messages.error(request, "Please fill out all required fields.")
            return render(request, 'myapp/registration/register.html')

        try:
            # Assuming height and weight are stored as DecimalFields in your model
            member = Member.objects.create(
                name=name,
                password=password,  # For demonstration; in real applications, use Django's user model & hash passwords
                fitness_goal=fitness_goals,
                height=height,
                weight=weight,
                health_metrics={}  # Assuming you have a default or an empty value for starters
            )
            # Redirect to login page or dashboard after successful registration
            return render(request, 'myapp/login/memberLogin.html')  # Assuming you have a URL named 'memberLogin'
        except Exception as e:
            messages.error(request, "An error occurred during registration. Please try again.")
            print(e)  # or use logging
            return render(request, 'myapp/registration/register.html')
    else:
        return render(request, 'myapp/registration/register.html')

def train_login(request):
    return render(request, 'myapp/login/trainerLogin.html')

def admin_login(request):
    return render(request, 'myapp/login/adminLogin.html')


def member_login(request):
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        password = request.POST.get('password').strip()

        # Assuming at least this query will be made
        try:
            member = Member.objects.get(name=name, password=password)
            # Print the last query, safely inside a conditional block ensuring at least one query was made
            print(connection.queries[-1])  # Safer usage
        except Member.DoesNotExist:
            # Print the last query, safely inside a conditional block ensuring at least one query was made
            print(connection.queries[-1])  # Safer usage
            return render(request, 'myapp/login/memberLogin.html', {'error': 'Invalid username or password'})
        
        # Print the last query, safely inside a conditional block ensuring at least one query was made
        print(connection.queries[-1])  # Safer usage
        
        request.session['member_id'] = member.member_id
        return render(request, 'myapp/dashboard/index.html')
    else:
        return render(request, 'myapp/login/memberLogin.html')
    

