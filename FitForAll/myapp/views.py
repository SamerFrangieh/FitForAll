import time
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import *
from django.db import connection
from datetime import date, datetime, timedelta
import os
 # Prints the last executed query
# #from .models import Book
# def member_login(request):
#     return render(request, 'myapp/login/memberLogin.html')


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Member
from django.db.models import Max

def register(request):
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        password = request.POST.get('password').strip()
        fitness_goals = request.POST.get('goals', '').strip() 
        height = request.POST.get('height').strip()
        weight = request.POST.get('weight').strip()

        if not (name and password and height and weight):
            messages.error(request, "Please fill out all required fields.")
            return render(request, 'myapp/registration/register.html')

        try:
            member = Member.objects.create(
                member_id= Member.objects.aggregate(Max('member_id'))['member_id__max']+1,
                name=name,
                password=password,  
                fitness_goal=fitness_goals,
                height=height,
                weight=weight,
                health_metrics={}  
            )
            return render(request, 'myapp/login/memberLogin.html')  
        except Exception as e:
            messages.error(request, "An error occurred during registration. Please try again.")
            print(e) 
            return render(request, 'myapp/registration/register.html')
    else:
        return render(request, 'myapp/registration/register.html')
    

def train_login(request):
    
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        password = request.POST.get('password').strip()

        try:
            trainer = Trainer.objects.get(name=name, password=password)
            
            print(connection.queries[-1])  
        except Trainer.DoesNotExist:
            print(connection.queries[-1])  
            return render(request, 'myapp/login/trainerLogin.html', {'error': 'Invalid username or password'})
        
        print(connection.queries[-1])  
        
        request.session['trainer_id'] = trainer.trainer_id
        return redirect('trainerDashboard')
    else:
        return render(request, 'myapp/login/trainerLogin.html')

#ADMIN METHODS --------------------------------------------------------
def admin_login(request):
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        password = request.POST.get('password').strip()

        try:
            admin = Admin.objects.get(name=name, password=password)
        except Admin.DoesNotExist:
            print(connection.queries[-1])  
            return render(request, 'myapp/login/adminLogin.html', {'error': 'Invalid username or password'})
        
        
        request.session['admin_id'] = admin.admin_id
        return redirect('adminDashboard')
    else:
        return render(request, 'myapp/login/adminLogin.html')
    
def adminDashboard(request):
    context = {}
    
    if request.method == 'POST':
        for key, value in request.POST.items():
            print(f"{key}: {value}")
        if 'delete' in request.POST:
            equipment_id = request.POST.get('delete')
            EquipmentMaintenance.objects.filter(equipment_id=equipment_id).delete() 
        elif 'update_status' in request.POST:
            equipment_id = request.POST.get('update_status')
            new_status = request.POST.get('status')
            equipment = EquipmentMaintenance.objects.get(equipment_id=equipment_id)
            equipment.status = new_status
            equipment.save() 
        elif 'add' in request.POST:
            name = request.POST.get('name')
            last_maintenance_date = request.POST.get('last_maintenance_date')
            next_maintenance_date = request.POST.get('next_maintenance_date')
            EquipmentMaintenance.objects.create(
                name=name,
                last_maintenance_date=last_maintenance_date,
                next_maintenance_date=next_maintenance_date
            ) 
        
        elif 'add_room_booking' in request.POST:
            room_id = request.POST.get('room_id')
            booking_date = request.POST.get('booking_date')
            start_time_str = request.POST.get('start_time')
            end_time_str = request.POST.get('end_time')

            room = Room.objects.get(room_id=room_id)
            start_datetime = datetime.strptime(f"{booking_date} {start_time_str}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{booking_date} {end_time_str}", "%Y-%m-%d %H:%M")

            RoomBooking.objects.create(
                room=room,
                start_time=start_datetime,
                end_time=end_datetime
            )
        if 'booking_id' in request.POST: 
            print(request.POST)
            booking_id = request.POST.get('booking_id')
            if request.POST.get('booking_type') == "Room Booking":

                RoomBooking.objects.filter(room_booking_id=booking_id).delete()
            else:

                GroupFitnessClass.objects.filter(group_fitness_class_id=booking_id).delete()
            messages.success(request, 'Booking successfully deleted.')
         # Handle payment management POST requests

        if 'payment_method' in request.POST:
            billing_id = request.POST.get('billing_id')
            payment_method = request.POST.get('payment_method')
            payment_date = datetime.now()  
            billing = Billing.objects.get(id=billing_id)
            Payment.objects.create(
                billing=billing,
                payment_date=payment_date,
                payment_method=payment_method,
                payment_status='successful'  
            )
            billing.status = 'paid'
            billing.save()

        if 'session_date' in request.POST:
            
    
            session_date = request.POST['session_date']
            print(f"Received session date from form: {session_date}")

            date_obj = datetime.strptime(session_date, '%Y-%m-%d').date()
            day_of_week = date_obj.weekday()+1
            print(f"Converted date to datetime object: {date_obj}, Day of week: {day_of_week}")

            available_trainers = TrainerAvailability.objects.filter(day_of_week=day_of_week)
            trainer_times = []

            print(f"Found {available_trainers.count()} trainers available on this day of the week.")

            for availability in available_trainers:
                occupied_times = []

                personal_sessions = PersonalSession.objects.filter(trainer=availability.trainer, date=date_obj)
                group_classes = GroupFitnessClass.objects.filter(trainer=availability.trainer, date=date_obj)
                
                for session in personal_sessions:
                    occupied_times.append((datetime.combine(date_obj, session.start_time), datetime.combine(date_obj, session.end_time)))

                for g_class in group_classes:
                    occupied_times.append((datetime.combine(date_obj, g_class.start_time), datetime.combine(date_obj, g_class.end_time)))

                start_datetime = datetime.combine(date_obj, availability.check_in)
                end_datetime = datetime.combine(date_obj, availability.check_out)

                while start_datetime + timedelta(hours=1) <= end_datetime:
                    if not any(start_datetime < block_end and start_datetime + timedelta(hours=1) > block_start for block_start, block_end in occupied_times):
                        trainer_times.append((availability.trainer, start_datetime.time().strftime('%H:%M')))
                        print(f"Added time slot for {availability.trainer.name} at {start_datetime.time().strftime('%H:%M')}")
                    start_datetime += timedelta(hours=1)
            context['available_trainers'] = trainer_times
            context['selected_date'] = session_date

            if not trainer_times:
                print("No available trainers found for the selected day.")

        if 'add_group_fitness_class' in request.POST:
            
            session_info = request.POST.get('trainer_session')
            trainer_id, time_str = session_info.split('|')
            room_id = request.POST.get('room_id')
            class_date = request.POST.get('date')
            start_time = datetime.strptime(time_str, '%H:%M').time()
            end_time = (datetime.combine(datetime.today(), start_time) + timedelta(hours=1)).time()
            GroupFitnessClass.objects.create(
                trainer_id=trainer_id,
                room_id=room_id,
                date=request.POST.get('session_date'),
                start_time=start_time,
                end_time=end_time
            )
            context['available_trainers'] = {}
            context['selected_date'] = {}
    equipments = EquipmentMaintenance.objects.all()
    rooms = Room.objects.all()
    room_bookings = RoomBooking.objects.select_related('room').order_by('start_time')
    group_fitness_bookings = GroupFitnessClass.objects.select_related('room').order_by('start_time')
    bills = Billing.objects.select_related('member').all()
    payments = Payment.objects.select_related('billing').all()

    combined_bookings = []
    for booking in room_bookings:
        booking_data = {
            'type': 'Room Booking',
            'booking': {
                'room_booking_id': booking.room_booking_id,
                'room': booking.room,
                'date': booking.start_time.date(),  
                'start_time': booking.start_time.time(),
                'end_time': booking.end_time.time()
            }
        }
        combined_bookings.append(booking_data)

    for booking in group_fitness_bookings:
        booking_data = {
            'type': 'Group Fitness Class',
            'booking': {
                
                'room_booking_id': booking.group_fitness_class_id,
                'room': booking.room,
                'date': booking.date,
                'start_time': booking.start_time,
                'end_time': booking.end_time
            }
        }
        combined_bookings.append(booking_data)

    context['equipments'] = equipments
    context['rooms'] = rooms
    context['bookings'] = combined_bookings
    context['bills'] = bills
    context['payments'] = payments


    return render(request, 'myapp/dashboard/adminDashboard.html', context)




def trainerDashboard(request):
    print("Loading trainer dashboard...")  
    days_of_week = {
        '0': 'Sunday', '1': 'Monday', '2': 'Tuesday',
        '3': 'Wednesday', '4': 'Thursday', '5': 'Friday', '6': 'Saturday'
    }
    hours = list(range(24))  
    members = []

    trainer_id = request.session.get('trainer_id')
    print(f"Session Trainer ID: {trainer_id}")  
    if not trainer_id:
        return redirect('trainerLogin')

    trainer = Trainer.objects.filter(trainer_id=trainer_id).first()
    if not trainer:
        return redirect('trainerLogin')
    print(f"Trainer fetched: {trainer.name}")  

    availabilities = TrainerAvailability.objects.filter(trainer=trainer).order_by('day_of_week')
    structured_availabilities = {
        day: {
            'checked': False,
            'check_in': None,
            'check_out': None
        } for day in days_of_week.values()
    }

    for availability in availabilities:
        day_key = days_of_week[str(availability.day_of_week)]
        structured_availabilities[day_key]['checked'] = True
        structured_availabilities[day_key]['check_in'] = availability.check_in.strftime('%H:00')
        structured_availabilities[day_key]['check_out'] = availability.check_out.strftime('%H:00')
    print(f"Structured availabilities: {structured_availabilities}")  

    if request.method == 'POST':
        print(f"POST data received: {request.POST}")  
        if 'member_name' in request.POST:
            member_name = request.POST.get('member_name', '')
            members = Member.objects.filter(name__icontains=member_name)
        else:
            days_selected = request.POST.getlist('days')
            for day_value in days_of_week.keys():
                day_name = days_of_week[day_value]
                check_in_time = request.POST.get(f'check_in_{day_value}', None)
                check_out_time = request.POST.get(f'check_out_{day_value}', None)
                print(f"Processing day {day_name}: Selected - {day_value in days_selected}, Check-in: {check_in_time}, Check-out: {check_out_time}")  # Debugging line
                if day_value in days_selected and check_in_time and check_out_time:
                    TrainerAvailability.objects.update_or_create(
                        trainer=trainer,
                        day_of_week=int(day_value),
                        defaults={
                            'check_in': f"{check_in_time}:00",
                            'check_out': f"{check_out_time}:00"
                        }
                    )
                elif day_value not in days_selected:
                    TrainerAvailability.objects.filter(trainer=trainer, day_of_week=int(day_value)).delete()
                
            messages.success(request, 'Your availability has been updated successfully!')
            return redirect('trainerDashboard')

    context = {
        'days_of_week': days_of_week,
        'hours': hours,
        'members': members,
        'availabilities': structured_availabilities
    }
    return render(request, 'myapp/dashboard/trainerDashboard.html', context)

def dashboard(request):
    if not request.session.get('member_id'):
        return redirect('memberLogin')

    member_id = request.session['member_id']
    try:
        member = Member.objects.get(member_id=member_id)
    except Member.DoesNotExist:
        return redirect('memberLogin')  

    context = {}


    if request.method == 'POST':
        if request.POST.get('diastolic')  is not None:
            member.diastolic_bp = request.POST.get('diastolic')
            member.systolic_bp = request.POST.get('systolic')
            if (member.diastolic_bp == '' or member.systolic_bp == ''):
                member.diastolic_bp =0
                member.systolic_bp = 0
            member.height = request.POST.get('Height')
            member.weight = request.POST.get('Weight')
            member.fitness_goal = request.POST.get('fitness_goals')
            member.act_levels = request.POST.get('act_levels')
            member.age = request.POST.get('Age')
            member.save()
            member = Member.objects.get(member_id=member_id)
            messages.success(request, "Profile updated successfully!")
        if 'session_date' in request.POST:
            
    
            session_date = request.POST['session_date']
            print(f"Received session date from form: {session_date}")

            date_obj = datetime.strptime(session_date, '%Y-%m-%d').date()
            day_of_week = date_obj.weekday()+1
            print(f"Converted date to datetime object: {date_obj}, Day of week: {day_of_week}")

            available_trainers = TrainerAvailability.objects.filter(day_of_week=day_of_week)
            trainer_times = []

            print(f"Found {available_trainers.count()} trainers available on this day of the week.")

            for availability in available_trainers:
                occupied_times = []

                personal_sessions = PersonalSession.objects.filter(trainer=availability.trainer, date=date_obj)
                group_classes = GroupFitnessClass.objects.filter(trainer=availability.trainer, date=date_obj)
                
                for session in personal_sessions:
                    occupied_times.append((datetime.combine(date_obj, session.start_time), datetime.combine(date_obj, session.end_time)))

                for g_class in group_classes:
                    occupied_times.append((datetime.combine(date_obj, g_class.start_time), datetime.combine(date_obj, g_class.end_time)))

                start_datetime = datetime.combine(date_obj, availability.check_in)
                end_datetime = datetime.combine(date_obj, availability.check_out)

                while start_datetime + timedelta(hours=1) <= end_datetime:
                    if not any(start_datetime < block_end and start_datetime + timedelta(hours=1) > block_start for block_start, block_end in occupied_times):
                        trainer_times.append((availability.trainer, start_datetime.time().strftime('%H:%M')))
                        print(f"Added time slot for {availability.trainer.name} at {start_datetime.time().strftime('%H:%M')}")
                    start_datetime += timedelta(hours=1)
            context['available_trainers'] = trainer_times
            context['selected_date'] = session_date

            if not trainer_times:
                print("No available trainers found for the selected day.")

        
        if 'trainer_session' in request.POST:
            print("Processing trainer and time selection form.")
            session_info = request.POST.get('trainer_session')
            if not session_info:
                print("No trainer or time selected; session_info is empty.")
                return HttpResponseBadRequest("Invalid trainer or time selected.")
            try:
                print(session_info)
                trainer_id, time_str = session_info.split('|')
                print(f"Received trainer ID: {trainer_id} and time: {time_str}")
            except ValueError as e:
                print(f"Error splitting session_info: {session_info}; Error: {str(e)}")
                return HttpResponseBadRequest("Invalid trainer or time format.")

            try:
                trainer = Trainer.objects.get(trainer_id=int(trainer_id))
            except Trainer.DoesNotExist:
                print(f"Trainer with ID {trainer_id} does not exist.")
                return HttpResponseBadRequest("Trainer not found.")
            except ValueError as e:
                print(f"Invalid trainer ID format: {trainer_id}; Error: {str(e)}")
                return HttpResponseBadRequest("Invalid trainer ID format.")

            try:
                start_time = datetime.strptime(time_str, '%H:%M').time()
                end_time = (datetime.combine(datetime.today(), start_time) + timedelta(hours=1)).time()
                print(f"Scheduled start time: {start_time}, end time: {end_time}")
            except ValueError as e:
                print(f"Error parsing time: {time_str}; Error: {str(e)}")
                return HttpResponseBadRequest("Invalid time format.")

            try:
                PersonalSession.objects.create(
                    trainer=trainer,
                    member=Member.objects.get(member_id=request.session['member_id']),
                    date=session_date,
                    start_time=start_time,
                    end_time=end_time
                )
                messages.success(request, "Session booked successfully!")
                print("Session booked successfully.")
            except Exception as e:
                print(f"Failed to create personal session; Error: {str(e)}")
                return HttpResponseBadRequest("Failed to book session.")
            context['available_trainers'] = {}
            context['selected_date'] = {}
        if request.POST.get('session_id') is not None:
            
            session_id = request.POST.get('session_id')
            try:
                session = PersonalSession.objects.get(personal_session_id=session_id)
                session.delete()
                messages.success(request, "Session cancelled successfully!")
            except PersonalSession.DoesNotExist:
                messages.error(request, "Session not found or already cancelled.")
        if request.POST.get('action') == 'enroll' and request.POST.get('class_id'):
                
            class_id = request.POST.get('class_id')
            group_class = GroupFitnessClass.objects.get(group_fitness_class_id=class_id)
            member = Member.objects.get(member_id=member_id)
            
            MemberGroupFitnessRegistration.objects.create(
                group_fitness_class=group_class,
                member=member
            )
            messages.success(request, "Enrolled in class successfully!")
        elif request.POST.get('action') == 'unenroll' and request.POST.get('class_id'):
                
            class_id = request.POST.get('class_id')
            group_class = GroupFitnessClass.objects.get(group_fitness_class_id=class_id)
            member = Member.objects.get(member_id=member_id)
            registration = MemberGroupFitnessRegistration.objects.filter(
                group_fitness_class=group_class,
                member=member
            )
            if registration.exists():
                registration.delete()
                messages.success(request, "Unenrolled from class successfully!")
            else:
                messages.error(request, "No enrollment to cancel.")

    group_fitness_classes = GroupFitnessClass.objects.all()
    classes_with_enrollment_status = []

    for group_class in group_fitness_classes:
        enrolled = MemberGroupFitnessRegistration.objects.filter(
            group_fitness_class=group_class,
            member_id=member_id
        ).exists()

        class_data = {
            'class': group_class,
            'enrolled': enrolled,
            'room_name': group_class.room.name, 
        }

        classes_with_enrollment_status.append(class_data)
    context['classes'] = classes_with_enrollment_status
    for key, value in request.POST.items():
        print(f"{key}: {value}")
    scheduled_sessions = PersonalSession.objects.filter(member_id=member_id).order_by('date', 'start_time')
    print(f"Found {len(scheduled_sessions)} scheduled sessions for member ID {member_id}")

        

    scheduled_sessions_list = []
    for session in scheduled_sessions:
        session_data = {
            'session_id': session.personal_session_id,
            'date': session.date,
            'trainer_name': session.trainer.name,
            'start_time': session.start_time.strftime("%H:%M"),
            'end_time': session.end_time.strftime("%H:%M")
        }
        scheduled_sessions_list.append(session_data)
        print(f"Session {session.personal_session_id}: {session_data}")
    context['scheduled_sessions'] = scheduled_sessions_list
                
    try:
        member.systolic_bp = int(member.systolic_bp)
    except ValueError:
        pass

    try:
        member.diastolic_bp = int(member.diastolic_bp)
    except ValueError:
        pass
    # Calculate BMI
    height_in_meters = float(member.height) / 100
    bmi = round(float(member.weight) / (height_in_meters ** 2), 1)
    bmi_category = ''
    if bmi < 19:
        bmi_category = 'Underweight 🟦'
    elif 19 <= bmi < 25:
        bmi_category = 'Healthy ✅'
    elif 25 <= bmi < 30:
        bmi_category = 'Overweight 🟨'
    elif 30 <= bmi < 40:
        bmi_category = 'Obese 🟧'
    else:
        bmi_category = 'Extremely Obese 🟥'

    # Calculate BMR
    bmr = 100
    rec_bmr = 100
    if member.age is None:
        member.age = 20
    bmr = int(round((88.362 + (13.397 * float(member.weight)) + (4.799 * float(member.height)) - (5.677 * float(member.age))),0))
    if member.act_levels == '1-3 x times a week':
        bmr = bmr + 800
    if member.act_levels == '3-5 x times a week':
        bmr = bmr + 1200
    if member.act_levels == '5-6 x times a week':
        bmr = bmr + 1600
    if member.act_levels == '6-7 x times a week':
        bmr = bmr + 1950
    rec_bmr = bmr

    if member.fitness_goal == 'lose_weight':
        rec_bmr = rec_bmr - 239
    
    if member.fitness_goal == 'gain_muscle':
        rec_bmr = rec_bmr + 226

    if member.fitness_goal == 'improve_endurance':
        rec_bmr = rec_bmr - 163

    if member.fitness_goal == 'increase_flexibility':
        rec_bmr = rec_bmr -121

    # Calculate BP rating
    bp_health = ''
    bp = str(member.systolic_bp) + '/' + str(member.diastolic_bp)
    if member.systolic_bp >= 180 or member.diastolic_bp >= 120:
        bp_health = 'High: Stage 2 Hypertension'
    elif 160 <= member.systolic_bp < 180 or 100 <= member.diastolic_bp < 110:
        bp_health = 'High: Stage 1 Hypertension'
    elif 140 <= member.systolic_bp < 160 or 90 <= member.diastolic_bp < 100:
        bp_health = 'Prehypertension'
    elif 120 <= member.systolic_bp < 140 and member.diastolic_bp < 90:
        bp_health = 'Normal'
    elif member.systolic_bp < 120 and member.diastolic_bp < 80:
        bp_health = 'Low'
    else:
        bp_health = 'Consult a doctor'

    #The workout schedules
    mon = ""
    tue = ''
    wed = ''
    thu = ''
    fri = ''
    sat = ''
    sun = ''

    if member.fitness_goal == 'gain_muscle':
        
        if member.act_levels == '1-3 x times a week':
            mon= 'Day 1: Push (Chest, Shoulders, and Triceps)//Bench Press - 4 sets of 8-12 reps,\n//Overhead Press - 3 sets of 8-12 reps,\n//Incline Dumbbell Press - 3 sets of 8-12 reps,\n//Lateral Raises - 3 sets of 12-15 reps,\n//Tricep Dips - 3 sets of 10-15 reps,//Tricep Pushdowns - 3 sets of 10-15 reps\n'
            tue = 'rest'
            wed = 'Day 2: Pull (Back, Biceps)//Deadlifts - 3 sets of 6-8 reps//Pull-ups - 3 sets of as many reps as possible//Barbell Rows - 3 sets of 8-12 reps//Face Pulls - 3 sets of 12-15 reps//Hammer Curls - 3 sets of 10-12 reps//Barbell Curls - 3 sets of 8-12 reps'
            thu = 'rest'
            fri = "Day 3: Legs (Quads, Hamstrings, and Calves)//Squats - 4 sets of 8-12 reps//Leg Press - 3 sets of 10-12 reps//Romanian Deadlifts - 3 sets of 8-12 reps//Leg Curls - 3 sets of 10-12 reps//Calf Raises - 5 sets of 12-15 reps"
            sat = 'rest'
            sun = 'rest'
        elif member.act_levels == '3-5 x times a week':
            mon= 'Day 1: Push (Chest, Shoulders, and Triceps)//Bench Press - 4 sets of 8-12 reps,\n//Overhead Press - 3 sets of 8-12 reps,\n//Incline Dumbbell Press - 3 sets of 8-12 reps,\n//Lateral Raises - 3 sets of 12-15 reps,\n//Tricep Dips - 3 sets of 10-15 reps,//Tricep Pushdowns - 3 sets of 10-15 reps\n'
            tue = 'rest'
            wed = 'Day 2: Pull (Back, Biceps)//Deadlifts - 3 sets of 6-8 reps//Pull-ups - 3 sets of as many reps as possible//Barbell Rows - 3 sets of 8-12 reps//Face Pulls - 3 sets of 12-15 reps//Hammer Curls - 3 sets of 10-12 reps//Barbell Curls - 3 sets of 8-12 reps'
            thu = 'Day 3: Arm Workout Day: Biceps and Triceps//Barbell Curl - 4 sets of 8-12 reps//Tricep Dips - 4 sets of 8-12 reps//Hammer Curls - 3 sets of 10-12 reps//Skull Crushers - 3 sets of 8-12 reps//Preacher Curl - 3 sets of 8-12 reps'
            fri = "Day 4: Legs (Quads, Hamstrings, and Calves)//Squats - 4 sets of 8-12 reps//Leg Press - 3 sets of 10-12 reps//Romanian Deadlifts - 3 sets of 8-12 reps//Leg Curls - 3 sets of 10-12 reps//Calf Raises - 5 sets of 12-15 reps"
            sat = 'rest'
            sun = 'rest'
        elif member.act_levels == '5-6 x times a week':
            mon= 'Day 1: Push (Chest, Shoulders, and Triceps)//Bench Press - 4 sets of 8-12 reps,\n//Overhead Press - 3 sets of 8-12 reps,\n//Incline Dumbbell Press - 3 sets of 8-12 reps,\n//Lateral Raises - 3 sets of 12-15 reps,\n//Tricep Dips - 3 sets of 10-15 reps,//Tricep Pushdowns - 3 sets of 10-15 reps\n'
            tue = 'Day 2: Pull (Back, Biceps)//Deadlifts - 3 sets of 6-8 reps//Pull-ups - 3 sets of as many reps as possible//Barbell Rows - 3 sets of 8-12 reps//Face Pulls - 3 sets of 12-15 reps//Hammer Curls - 3 sets of 10-12 reps//Barbell Curls - 3 sets of 8-12 reps'
            wed = "Day 3: Legs (Quads, Hamstrings, and Calves)//Squats - 4 sets of 8-12 reps//Leg Press - 3 sets of 10-12 reps//Romanian Deadlifts - 3 sets of 8-12 reps//Leg Curls - 3 sets of 10-12 reps//Calf Raises - 5 sets of 12-15 reps"
            thu = 'Day 4: Push (Chest, Shoulders, and Triceps)//Bench Press - 4 sets of 8-12 reps,\n//Overhead Press - 3 sets of 8-12 reps,\n//Incline Dumbbell Press - 3 sets of 8-12 reps,\n//Lateral Raises - 3 sets of 12-15 reps,\n//Tricep Dips - 3 sets of 10-15 reps,//Tricep Pushdowns - 3 sets of 10-15 reps\n'
            fri = 'Day 5: Pull (Back, Biceps)//Deadlifts - 3 sets of 6-8 reps//Pull-ups - 3 sets of as many reps as possible//Barbell Rows - 3 sets of 8-12 reps//Face Pulls - 3 sets of 12-15 reps//Hammer Curls - 3 sets of 10-12 reps//Barbell Curls - 3 sets of 8-12 reps'
            sat = "Day 6: Legs (Quads, Hamstrings, and Calves)//Squats - 4 sets of 8-12 reps//Leg Press - 3 sets of 10-12 reps//Romanian Deadlifts - 3 sets of 8-12 reps//Leg Curls - 3 sets of 10-12 reps//Calf Raises - 5 sets of 12-15 reps"
            sun = 'rest'
        elif member.act_levels =='6-7 x times a week':
            mon= 'Day 1: Push (Chest, Shoulders, and Triceps)//Bench Press - 4 sets of 8-12 reps,\n//Overhead Press - 3 sets of 8-12 reps,\n//Incline Dumbbell Press - 3 sets of 8-12 reps,\n//Lateral Raises - 3 sets of 12-15 reps,\n//Tricep Dips - 3 sets of 10-15 reps,//Tricep Pushdowns - 3 sets of 10-15 reps\n'
            tue = 'Day 2: Pull (Back, Biceps)//Deadlifts - 3 sets of 6-8 reps//Pull-ups - 3 sets of as many reps as possible//Barbell Rows - 3 sets of 8-12 reps//Face Pulls - 3 sets of 12-15 reps//Hammer Curls - 3 sets of 10-12 reps//Barbell Curls - 3 sets of 8-12 reps'
            wed = "Day 3: Legs (Quads, Hamstrings, and Calves)//Squats - 4 sets of 8-12 reps//Leg Press - 3 sets of 10-12 reps//Romanian Deadlifts - 3 sets of 8-12 reps//Leg Curls - 3 sets of 10-12 reps//Calf Raises - 5 sets of 12-15 reps"
            thu = 'Day 4: Push (Chest, Shoulders, and Triceps)//Bench Press - 4 sets of 8-12 reps,\n//Overhead Press - 3 sets of 8-12 reps,\n//Incline Dumbbell Press - 3 sets of 8-12 reps,\n//Lateral Raises - 3 sets of 12-15 reps,\n//Tricep Dips - 3 sets of 10-15 reps,//Tricep Pushdowns - 3 sets of 10-15 reps\n'
            fri = 'Day 5: Pull (Back, Biceps)//Deadlifts - 3 sets of 6-8 reps//Pull-ups - 3 sets of as many reps as possible//Barbell Rows - 3 sets of 8-12 reps//Face Pulls - 3 sets of 12-15 reps//Hammer Curls - 3 sets of 10-12 reps//Barbell Curls - 3 sets of 8-12 reps'
            sat = "Day 6: Legs (Quads, Hamstrings, and Calves)//Squats - 4 sets of 8-12 reps//Leg Press - 3 sets of 10-12 reps//Romanian Deadlifts - 3 sets of 8-12 reps//Leg Curls - 3 sets of 10-12 reps//Calf Raises - 5 sets of 12-15 reps"
            sun = 'Day 7: Arm Workout Day: Biceps and Triceps//Barbell Curl - 4 sets of 8-12 reps//Tricep Dips - 4 sets of 8-12 reps//Hammer Curls - 3 sets of 10-12 reps//Skull Crushers - 3 sets of 8-12 reps//Preacher Curl - 3 sets of 8-12 reps'
        
    elif member.fitness_goal == 'lose_weight':
        if member.act_levels == '1-3 x times a week':
            mon= 'Day 1: Cardio and Core//Treadmill Running - 30 minutes at a moderate pace//Cycling - 20 minutes at a vigorous pace//Russian Twists - 4 sets of 15 reps each side//Leg Raises - 4 sets of 12 reps'
            tue = 'rest'
            wed = 'Day 2: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            thu = 'rest'
            fri = "Day 3: High-Intensity Interval Training (HIIT)//Sprints - 10 rounds of 30 seconds sprint/30 seconds rest//Burpees - 5 sets of 20 seconds on/40 seconds rest//Jump Rope - 10 minutes with intervals of 1 minute on/1 minute off"
            sat = 'rest'
            sun = 'rest'
        elif member.act_levels == '3-5 x times a week':
            mon= 'Day 1: Cardio and Core//Treadmill Running - 30 minutes at a moderate pace//Cycling - 20 minutes at a vigorous pace//Russian Twists - 4 sets of 15 reps each side//Leg Raises - 4 sets of 12 reps'
            tue = 'rest'
            wed = 'Day 2: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            thu = 'rest'
            fri = "Day 3: High-Intensity Interval Training (HIIT)//Sprints - 10 rounds of 30 seconds sprint/30 seconds rest//Burpees - 5 sets of 20 seconds on/40 seconds rest//Jump Rope - 10 minutes with intervals of 1 minute on/1 minute off"
            sat = 'Day 4: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            sun = 'rest'
        elif member.act_levels == '5-6 x times a week':
            mon= 'Day 1: Cardio and Core//Treadmill Running - 30 minutes at a moderate pace//Cycling - 20 minutes at a vigorous pace//Russian Twists - 4 sets of 15 reps each side//Leg Raises - 4 sets of 12 reps'
            tue = 'Day 2: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            wed = 'Day 3: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            thu = 'rest'
            fri = "Day 4: High-Intensity Interval Training (HIIT)//Sprints - 10 rounds of 30 seconds sprint/30 seconds rest//Burpees - 5 sets of 20 seconds on/40 seconds rest//Jump Rope - 10 minutes with intervals of 1 minute on/1 minute off"
            sat = 'Day 5: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            sun = 'rest'
        elif member.act_levels =='6-7 x times a week':
            mon= 'Day 1: Cardio and Core//Treadmill Running - 30 minutes at a moderate pace//Cycling - 20 minutes at a vigorous pace//Russian Twists - 4 sets of 15 reps each side//Leg Raises - 4 sets of 12 reps'
            tue = 'Day 2: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            wed = 'Day 3: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            thu = 'Day 6: Active RecoveryYoga - 60 minutes focusing on flexibility and core//Light Walking - 30 minutes at a gentle pace'
            fri = "Day 4: High-Intensity Interval Training (HIIT)//Sprints - 10 rounds of 30 seconds sprint/30 seconds rest//Burpees - 5 sets of 20 seconds on/40 seconds rest//Jump Rope - 10 minutes with intervals of 1 minute on/1 minute off"
            sat = 'Day 5: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            sun = 'rest'

    elif member.fitness_goal == 'improve_endurance':
        if member.act_levels == '1-3 x times a week':
            mon = "Day 1: Cardio Intervals//Treadmill or Outdoor Running - 30 minutes of interval training (1 min fast/2 min slow)"
            tue = "rest"
            wed = "Day 2: Full Body Circuit//Bodyweight Exercises (Push-ups, Pull-ups, Squats) - 3 rounds of 15 reps each"
            thu = "rest"
            fri = "Day 3: Long Duration Cardio//Cycling or Swimming - 45 minutes at a steady pace"
            sat = "rest"
            sun = "rest"

        elif member.act_levels == '3-5 x times a week':
            mon = "Day 1: High Intensity Interval Training//HIIT - 20 minutes (30s high intensity/30s low intensity)"
            tue = "rest"
            wed = "Day 2: Strength and Endurance Circuit//Mix of Weight Lifting and Bodyweight Exercises - 3 sets of 12 reps"
            thu = "Day 3: Cardio Intervals//Rowing Machine or Jump Rope - 20 minutes of interval training"
            fri = "rest"
            sat = "Day 4: Long Duration Cardio//Jogging - 60 minutes at a moderate pace"
            sun = "rest"

        elif member.act_levels == '5-6 x times a week':
            mon = "Day 1: Cardio Intervals//Treadmill Sprints - 30 minutes of interval training (1 min sprint/2 min walk)"
            tue = "Day 2: Circuit Training//Full body circuit with resistance bands - 3 circuits of 10 mins each"
            wed = "rest"
            thu = "Day 3: Strength Training//Bodyweight strength exercises - 4 sets of 10-12 reps"
            fri = "Day 4: Cardio Endurance//Steady State Cycling - 50 minutes at a moderate intensity"
            sat = "Day 5: Active Recovery//Yoga or light stretching - 30 minutes"
            sun = "rest"

        elif member.act_levels == '6-7 x times a week':
            mon = "Day 1: Interval Training//Treadmill intervals - 25 minutes (3 min run/2 min walk)"
            tue = "Day 2: Circuit Training//Kettlebell circuit - 4 sets of 15 reps"
            wed = "Day 3: Endurance Cardio//Long distance running - 60 minutes at a steady pace"
            thu = "Day 4: High-Intensity Bodyweight//Tabata style - 20 minutes (20s work/10s rest)"
            fri = "Day 5: Strength Focus//Compound lifting - Squats, Deadlifts, Bench Press - 3 sets of 8-12 reps"
            sat = "Day 6: Mixed Cardio//Rowing and Cycling - 45 minutes total"
            sun = "Day 7: Active Rest//Stretching and foam rolling - 30 minutes"

    if member.fitness_goal == 'increase_flexibility':
        if member.act_levels == '1-3 x times a week':
            mon = "Day 1: Yoga Stretching//Full body yoga - 30 minutes"
            tue = "rest"
            wed = "Day 2: Dynamic Stretching//Full body dynamic stretches - 20 minutes"
            thu = "rest"
            fri = "Day 3: Pilates//Beginner Pilates session - 30 minutes"
            sat = "rest"
            sun = "rest"

        elif member.act_levels == '3-5 x times a week':
            mon = "Day 1: Yoga Stretching//Full body yoga - 45 minutes"
            tue = "rest"
            wed = "Day 2: Dynamic Stretching//Leg and hip dynamic stretches - 20 minutes"
            thu = "Day 3: Tai Chi//Beginner Tai Chi class - 30 minutes"
            fri = "rest"
            sat = "Day 4: Pilates//Intermediate Pilates session - 40 minutes"
            sun = "rest"

        elif member.act_levels == '5-6 x times a week':
            mon = "Day 1: Yoga Stretching//Advanced yoga poses - 45 minutes"
            tue = "Day 2: Pilates//Core-focused Pilates - 40 minutes"
            wed = "rest"
            thu = "Day 3: Dynamic Stretching//Full body dynamic stretches - 30 minutes"
            fri = "Day 4: Tai Chi//Intermediate Tai Chi session - 45 minutes"
            sat = "Day 5: Active Recovery//Light yoga and meditation - 30 minutes"
            sun = "rest"

        elif member.act_levels == '6-7 x times a week':
            mon = "Day 1: Yoga Stretching//Intensive yoga session - 60 minutes"
            tue = "Day 2: Dynamic Stretching//Sports specific stretches - 30 minutes"
            wed = "Day 3: Pilates//Advanced Pilates session - 45 minutes"
            thu = "Day 4: Yoga Stretching//Power yoga - 45 minutes"
            fri = "Day 5: Tai Chi//Advanced Tai Chi practice - 60 minutes"
            sat = "Day 6: Dynamic Stretching//Injury prevention stretches - 30 minutes"
            sun = "Day 7: Active Rest//Gentle yoga and deep breathing - 30 minutes"

    #namem position
    name_pos = member.name

    #achievements
    bmi_good = ''
    bp_normal = ''
    if bp_health =='Normal':
        bp_normal = '🥇Achieved a healthy Blood pressure'

    if bmi_category == 'Healthy ✅':
        bmi_good = '🥇Healthy BMI'

    if bmr!=100:
        bmr_achieve = '🥇You have found your BMR'

    lose=''
    gain = ''
    flex=''
    run=''

    if member.fitness_goal == 'lose_weight':
        lose = '🥇You are losing weight'
    elif member.fitness_goal == 'gain_muscle':
        gain = '🥇You are gaining muscle'
    elif member.fitness_goal == 'improve_endurance':
        run = '🥇 Your endurance is improving'
    elif member.fitness_goal=='increase_flexibility':
        flex='🥇 Getting more flexible'
    
    context['member'] = member
    context['bmi'] = bmi
    context['bmi_category'] = bmi_category
    context['bp_health'] = bp_health
    context['bp'] = bp
    context['bmr'] = bmr
    context['rec_bmr'] = rec_bmr
    context['mon'] = mon
    context['tue'] = tue
    context['wed'] = wed
    context['thu'] = thu
    context['fri'] = fri
    context['sat'] = sat
    context['sun'] = sun
    context['name_pos'] = name_pos
    context['bmi_good'] = bmi_good
    context['bp_normal'] = bp_normal
    context['bmr_achieve'] = bmr_achieve
    context['lose'] = lose
    context['gain'] = gain
    context['run'] = run
    context['flex'] = flex

    return render(request, 'myapp/dashboard/index.html', context)



def member_profile(request, member_id):
    try:
        member = Member.objects.get(member_id=member_id)
    except Member.DoesNotExist:
        return redirect('memberLogin')  
    context = {}

    if request.method == 'POST':
        if request.POST.get('diastolic')  is not None:
            member.diastolic_bp = request.POST.get('diastolic')
            member.systolic_bp = request.POST.get('systolic')
            if (member.diastolic_bp == '' or member.systolic_bp == ''):
                member.diastolic_bp =0
                member.systolic_bp = 0
            member.height = request.POST.get('Height')
            member.weight = request.POST.get('Weight')
            member.fitness_goal = request.POST.get('fitness_goals')
            member.act_levels = request.POST.get('act_levels')
            member.age = request.POST.get('Age')
            member.save()
            messages.success(request, "Profile updated successfully!")
        if 'session_date' in request.POST:
            
            session_date = request.POST['session_date']
            print(f"Received session date from form: {session_date}")

            date_obj = datetime.strptime(session_date, '%Y-%m-%d').date()
            day_of_week = date_obj.weekday()+1
            print(f"Converted date to datetime object: {date_obj}, Day of week: {day_of_week}")

            available_trainers = TrainerAvailability.objects.filter(day_of_week=day_of_week)
            trainer_times = []

            print(f"Found {available_trainers.count()} trainers available on this day of the week.")

            for availability in available_trainers:
                if not PersonalSession.objects.filter(trainer=availability.trainer, date=date_obj).exists():
                    full_day = datetime.combine(date_obj, datetime.min.time())  
                    start_datetime = datetime.combine(date_obj, availability.check_in)
                    end_datetime = datetime.combine(date_obj, availability.check_out)

                    print(f"Trainer {availability.trainer.name} is available from {start_datetime.time()} to {end_datetime.time()}")

                    while start_datetime + timedelta(hours=1) <= end_datetime:
                        trainer_times.append((availability.trainer, start_datetime.time().strftime('%H:%M')))
                        print(f"Added time slot for {availability.trainer.name} at {start_datetime.time().strftime('%H:%M')}")
                        start_datetime += timedelta(hours=1)

            context['available_trainers'] = trainer_times
            context['selected_date'] = session_date

            if not trainer_times:
                print("No available trainers found for the selected day.")

        
        if 'trainer_session' in request.POST:
            print("Processing trainer and time selection form.")
            session_info = request.POST.get('trainer_session')
            if not session_info:
                print("No trainer or time selected; session_info is empty.")
                return HttpResponseBadRequest("Invalid trainer or time selected.")
            try:
                print(session_info)
                trainer_id, time_str = session_info.split('|')
                print(f"Received trainer ID: {trainer_id} and time: {time_str}")
            except ValueError as e:
                print(f"Error splitting session_info: {session_info}; Error: {str(e)}")
                return HttpResponseBadRequest("Invalid trainer or time format.")

            try:
                trainer = Trainer.objects.get(trainer_id=int(trainer_id))
            except Trainer.DoesNotExist:
                print(f"Trainer with ID {trainer_id} does not exist.")
                return HttpResponseBadRequest("Trainer not found.")
            except ValueError as e:
                print(f"Invalid trainer ID format: {trainer_id}; Error: {str(e)}")
                return HttpResponseBadRequest("Invalid trainer ID format.")

            try:
                start_time = datetime.strptime(time_str, '%H:%M').time()
                end_time = (datetime.combine(datetime.today(), start_time) + timedelta(hours=1)).time()
                print(f"Scheduled start time: {start_time}, end time: {end_time}")
            except ValueError as e:
                print(f"Error parsing time: {time_str}; Error: {str(e)}")
                return HttpResponseBadRequest("Invalid time format.")

            try:
                PersonalSession.objects.create(
                    trainer=trainer,
                    member=Member.objects.get(member_id=request.session['member_id']),
                    date=session_date,
                    start_time=start_time,
                    end_time=end_time
                )
                messages.success(request, "Session booked successfully!")
                print("Session booked successfully.")
            except Exception as e:
                print(f"Failed to create personal session; Error: {str(e)}")
                return HttpResponseBadRequest("Failed to book session.")
        if request.POST.get('session_id') is not None:
            
            session_id = request.POST.get('session_id')
            try:
                session = PersonalSession.objects.get(personal_session_id=session_id)
                session.delete()
                messages.success(request, "Session cancelled successfully!")
            except PersonalSession.DoesNotExist:
                messages.error(request, "Session not found or already cancelled.")
        if request.POST.get('action') == 'enroll' and request.POST.get('class_id'):
                
            class_id = request.POST.get('class_id')
            group_class = GroupFitnessClass.objects.get(group_fitness_class_id=class_id)
            member = Member.objects.get(member_id=member_id)
            
            MemberGroupFitnessRegistration.objects.create(
                group_fitness_class=group_class,
                member=member
            )
            messages.success(request, "Enrolled in class successfully!")
        elif request.POST.get('action') == 'unenroll' and request.POST.get('class_id'):
                
            class_id = request.POST.get('class_id')
            group_class = GroupFitnessClass.objects.get(group_fitness_class_id=class_id)
            member = Member.objects.get(member_id=member_id)
            registration = MemberGroupFitnessRegistration.objects.filter(
                group_fitness_class=group_class,
                member=member
            )
            if registration.exists():
                registration.delete()
                messages.success(request, "Unenrolled from class successfully!")
            else:
                messages.error(request, "No enrollment to cancel.")

    group_fitness_classes = GroupFitnessClass.objects.all()
    classes_with_enrollment_status = []

    for group_class in group_fitness_classes:
        enrolled = MemberGroupFitnessRegistration.objects.filter(
            group_fitness_class=group_class,
            member_id=member_id
        ).exists()

        class_data = {
            'class': group_class,
            'enrolled': enrolled,
            'room_name': group_class.room.name, 
        }

        classes_with_enrollment_status.append(class_data)
    context['classes'] = classes_with_enrollment_status
    for key, value in request.POST.items():
        print(f"{key}: {value}")
    scheduled_sessions = PersonalSession.objects.filter(member_id=member_id).order_by('date', 'start_time')
    print(f"Found {len(scheduled_sessions)} scheduled sessions for member ID {member_id}")

        

    scheduled_sessions_list = []
    for session in scheduled_sessions:
        session_data = {
            'session_id': session.personal_session_id,
            'date': session.date,
            'trainer_name': session.trainer.name,
            'start_time': session.start_time.strftime("%H:%M"),
            'end_time': session.end_time.strftime("%H:%M")
        }
        scheduled_sessions_list.append(session_data)
        print(f"Session {session.personal_session_id}: {session_data}")
    context['scheduled_sessions'] = scheduled_sessions_list
                
    try:
        member.systolic_bp = int(member.systolic_bp)
    except ValueError:
        pass

    try:
        member.diastolic_bp = int(member.diastolic_bp)
    except ValueError:
        pass
    # Calculate BMI
    height_in_meters = float(member.height) / 100
    bmi = round(float(member.weight) / (height_in_meters ** 2), 1)
    bmi_category = ''
    if bmi < 19:
        bmi_category = 'Underweight 🟦'
    elif 19 <= bmi < 25:
        bmi_category = 'Healthy ✅'
    elif 25 <= bmi < 30:
        bmi_category = 'Overweight 🟨'
    elif 30 <= bmi < 40:
        bmi_category = 'Obese 🟧'
    else:
        bmi_category = 'Extremely Obese 🟥'

    # Calculate BMR
    bmr = 100
    rec_bmr = 100
    if member.age is None:
        member.age = 20
    bmr = int(round((88.362 + (13.397 * float(member.weight)) + (4.799 * float(member.height)) - (5.677 * float(member.age))),0))
    if member.act_levels == '1-3 x times a week':
        bmr = bmr + 800
    if member.act_levels == '3-5 x times a week':
        bmr = bmr + 1200
    if member.act_levels == '5-6 x times a week':
        bmr = bmr + 1600
    if member.act_levels == '6-7 x times a week':
        bmr = bmr + 1950

    rec_bmr = bmr

    if member.fitness_goal == 'lose_weight':
        rec_bmr = rec_bmr - 239
    
    if member.fitness_goal == 'gain_muscle':
        rec_bmr = rec_bmr + 226

    if member.fitness_goal == 'improve_endurance':
        rec_bmr = rec_bmr - 163

    if member.fitness_goal == 'increase_flexibility':
        rec_bmr = rec_bmr -121

    # Calculate BP rating
    bp_health = ''
    bp = str(member.systolic_bp) + '/' + str(member.diastolic_bp)
    if member.systolic_bp >= 180 or member.diastolic_bp >= 120:
        bp_health = 'High: Stage 2 Hypertension'
    elif 160 <= member.systolic_bp < 180 or 100 <= member.diastolic_bp < 110:
        bp_health = 'High: Stage 1 Hypertension'
    elif 140 <= member.systolic_bp < 160 or 90 <= member.diastolic_bp < 100:
        bp_health = 'Prehypertension'
    elif 120 <= member.systolic_bp < 140 and member.diastolic_bp < 90:
        bp_health = 'Normal'
    elif member.systolic_bp < 120 and member.diastolic_bp < 80:
        bp_health = 'Low'
    else:
        bp_health = 'Consult a doctor'

    #The workout schedules
    mon = ""
    tue = ''
    wed = ''
    thu = ''
    fri = ''
    sat = ''
    sun = ''

    if member.fitness_goal == 'gain_muscle':
        
        if member.act_levels == '1-3 x times a week':
            mon= 'Day 1: Push (Chest, Shoulders, and Triceps)//Bench Press - 4 sets of 8-12 reps,\n//Overhead Press - 3 sets of 8-12 reps,\n//Incline Dumbbell Press - 3 sets of 8-12 reps,\n//Lateral Raises - 3 sets of 12-15 reps,\n//Tricep Dips - 3 sets of 10-15 reps,//Tricep Pushdowns - 3 sets of 10-15 reps\n'
            tue = 'rest'
            wed = 'Day 2: Pull (Back, Biceps)//Deadlifts - 3 sets of 6-8 reps//Pull-ups - 3 sets of as many reps as possible//Barbell Rows - 3 sets of 8-12 reps//Face Pulls - 3 sets of 12-15 reps//Hammer Curls - 3 sets of 10-12 reps//Barbell Curls - 3 sets of 8-12 reps'
            thu = 'rest'
            fri = "Day 3: Legs (Quads, Hamstrings, and Calves)//Squats - 4 sets of 8-12 reps//Leg Press - 3 sets of 10-12 reps//Romanian Deadlifts - 3 sets of 8-12 reps//Leg Curls - 3 sets of 10-12 reps//Calf Raises - 5 sets of 12-15 reps"
            sat = 'rest'
            sun = 'rest'
        elif member.act_levels == '3-5 x times a week':
            mon= 'Day 1: Push (Chest, Shoulders, and Triceps)//Bench Press - 4 sets of 8-12 reps,\n//Overhead Press - 3 sets of 8-12 reps,\n//Incline Dumbbell Press - 3 sets of 8-12 reps,\n//Lateral Raises - 3 sets of 12-15 reps,\n//Tricep Dips - 3 sets of 10-15 reps,//Tricep Pushdowns - 3 sets of 10-15 reps\n'
            tue = 'rest'
            wed = 'Day 2: Pull (Back, Biceps)//Deadlifts - 3 sets of 6-8 reps//Pull-ups - 3 sets of as many reps as possible//Barbell Rows - 3 sets of 8-12 reps//Face Pulls - 3 sets of 12-15 reps//Hammer Curls - 3 sets of 10-12 reps//Barbell Curls - 3 sets of 8-12 reps'
            thu = 'Day 3: Arm Workout Day: Biceps and Triceps//Barbell Curl - 4 sets of 8-12 reps//Tricep Dips - 4 sets of 8-12 reps//Hammer Curls - 3 sets of 10-12 reps//Skull Crushers - 3 sets of 8-12 reps//Preacher Curl - 3 sets of 8-12 reps'
            fri = "Day 4: Legs (Quads, Hamstrings, and Calves)//Squats - 4 sets of 8-12 reps//Leg Press - 3 sets of 10-12 reps//Romanian Deadlifts - 3 sets of 8-12 reps//Leg Curls - 3 sets of 10-12 reps//Calf Raises - 5 sets of 12-15 reps"
            sat = 'rest'
            sun = 'rest'
        elif member.act_levels == '5-6 x times a week':
            mon= 'Day 1: Push (Chest, Shoulders, and Triceps)//Bench Press - 4 sets of 8-12 reps,\n//Overhead Press - 3 sets of 8-12 reps,\n//Incline Dumbbell Press - 3 sets of 8-12 reps,\n//Lateral Raises - 3 sets of 12-15 reps,\n//Tricep Dips - 3 sets of 10-15 reps,//Tricep Pushdowns - 3 sets of 10-15 reps\n'
            tue = 'Day 2: Pull (Back, Biceps)//Deadlifts - 3 sets of 6-8 reps//Pull-ups - 3 sets of as many reps as possible//Barbell Rows - 3 sets of 8-12 reps//Face Pulls - 3 sets of 12-15 reps//Hammer Curls - 3 sets of 10-12 reps//Barbell Curls - 3 sets of 8-12 reps'
            wed = "Day 3: Legs (Quads, Hamstrings, and Calves)//Squats - 4 sets of 8-12 reps//Leg Press - 3 sets of 10-12 reps//Romanian Deadlifts - 3 sets of 8-12 reps//Leg Curls - 3 sets of 10-12 reps//Calf Raises - 5 sets of 12-15 reps"
            thu = 'Day 4: Push (Chest, Shoulders, and Triceps)//Bench Press - 4 sets of 8-12 reps,\n//Overhead Press - 3 sets of 8-12 reps,\n//Incline Dumbbell Press - 3 sets of 8-12 reps,\n//Lateral Raises - 3 sets of 12-15 reps,\n//Tricep Dips - 3 sets of 10-15 reps,//Tricep Pushdowns - 3 sets of 10-15 reps\n'
            fri = 'Day 5: Pull (Back, Biceps)//Deadlifts - 3 sets of 6-8 reps//Pull-ups - 3 sets of as many reps as possible//Barbell Rows - 3 sets of 8-12 reps//Face Pulls - 3 sets of 12-15 reps//Hammer Curls - 3 sets of 10-12 reps//Barbell Curls - 3 sets of 8-12 reps'
            sat = "Day 6: Legs (Quads, Hamstrings, and Calves)//Squats - 4 sets of 8-12 reps//Leg Press - 3 sets of 10-12 reps//Romanian Deadlifts - 3 sets of 8-12 reps//Leg Curls - 3 sets of 10-12 reps//Calf Raises - 5 sets of 12-15 reps"
            sun = 'rest'
        elif member.act_levels =='6-7 x times a week':
            mon= 'Day 1: Push (Chest, Shoulders, and Triceps)//Bench Press - 4 sets of 8-12 reps,\n//Overhead Press - 3 sets of 8-12 reps,\n//Incline Dumbbell Press - 3 sets of 8-12 reps,\n//Lateral Raises - 3 sets of 12-15 reps,\n//Tricep Dips - 3 sets of 10-15 reps,//Tricep Pushdowns - 3 sets of 10-15 reps\n'
            tue = 'Day 2: Pull (Back, Biceps)//Deadlifts - 3 sets of 6-8 reps//Pull-ups - 3 sets of as many reps as possible//Barbell Rows - 3 sets of 8-12 reps//Face Pulls - 3 sets of 12-15 reps//Hammer Curls - 3 sets of 10-12 reps//Barbell Curls - 3 sets of 8-12 reps'
            wed = "Day 3: Legs (Quads, Hamstrings, and Calves)//Squats - 4 sets of 8-12 reps//Leg Press - 3 sets of 10-12 reps//Romanian Deadlifts - 3 sets of 8-12 reps//Leg Curls - 3 sets of 10-12 reps//Calf Raises - 5 sets of 12-15 reps"
            thu = 'Day 4: Push (Chest, Shoulders, and Triceps)//Bench Press - 4 sets of 8-12 reps,\n//Overhead Press - 3 sets of 8-12 reps,\n//Incline Dumbbell Press - 3 sets of 8-12 reps,\n//Lateral Raises - 3 sets of 12-15 reps,\n//Tricep Dips - 3 sets of 10-15 reps,//Tricep Pushdowns - 3 sets of 10-15 reps\n'
            fri = 'Day 5: Pull (Back, Biceps)//Deadlifts - 3 sets of 6-8 reps//Pull-ups - 3 sets of as many reps as possible//Barbell Rows - 3 sets of 8-12 reps//Face Pulls - 3 sets of 12-15 reps//Hammer Curls - 3 sets of 10-12 reps//Barbell Curls - 3 sets of 8-12 reps'
            sat = "Day 6: Legs (Quads, Hamstrings, and Calves)//Squats - 4 sets of 8-12 reps//Leg Press - 3 sets of 10-12 reps//Romanian Deadlifts - 3 sets of 8-12 reps//Leg Curls - 3 sets of 10-12 reps//Calf Raises - 5 sets of 12-15 reps"
            sun = 'Day 7: Arm Workout Day: Biceps and Triceps//Barbell Curl - 4 sets of 8-12 reps//Tricep Dips - 4 sets of 8-12 reps//Hammer Curls - 3 sets of 10-12 reps//Skull Crushers - 3 sets of 8-12 reps//Preacher Curl - 3 sets of 8-12 reps'
        
    elif member.fitness_goal == 'lose_weight':
        if member.act_levels == '1-3 x times a week':
            mon= 'Day 1: Cardio and Core//Treadmill Running - 30 minutes at a moderate pace//Cycling - 20 minutes at a vigorous pace//Russian Twists - 4 sets of 15 reps each side//Leg Raises - 4 sets of 12 reps'
            tue = 'rest'
            wed = 'Day 2: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            thu = 'rest'
            fri = "Day 3: High-Intensity Interval Training (HIIT)//Sprints - 10 rounds of 30 seconds sprint/30 seconds rest//Burpees - 5 sets of 20 seconds on/40 seconds rest//Jump Rope - 10 minutes with intervals of 1 minute on/1 minute off"
            sat = 'rest'
            sun = 'rest'
        elif member.act_levels == '3-5 x times a week':
            mon= 'Day 1: Cardio and Core//Treadmill Running - 30 minutes at a moderate pace//Cycling - 20 minutes at a vigorous pace//Russian Twists - 4 sets of 15 reps each side//Leg Raises - 4 sets of 12 reps'
            tue = 'rest'
            wed = 'Day 2: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            thu = 'rest'
            fri = "Day 3: High-Intensity Interval Training (HIIT)//Sprints - 10 rounds of 30 seconds sprint/30 seconds rest//Burpees - 5 sets of 20 seconds on/40 seconds rest//Jump Rope - 10 minutes with intervals of 1 minute on/1 minute off"
            sat = 'Day 4: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            sun = 'rest'
        elif member.act_levels == '5-6 x times a week':
            mon= 'Day 1: Cardio and Core//Treadmill Running - 30 minutes at a moderate pace//Cycling - 20 minutes at a vigorous pace//Russian Twists - 4 sets of 15 reps each side//Leg Raises - 4 sets of 12 reps'
            tue = 'Day 2: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            wed = 'Day 3: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            thu = 'rest'
            fri = "Day 4: High-Intensity Interval Training (HIIT)//Sprints - 10 rounds of 30 seconds sprint/30 seconds rest//Burpees - 5 sets of 20 seconds on/40 seconds rest//Jump Rope - 10 minutes with intervals of 1 minute on/1 minute off"
            sat = 'Day 5: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            sun = 'rest'
        elif member.act_levels =='6-7 x times a week':
            mon= 'Day 1: Cardio and Core//Treadmill Running - 30 minutes at a moderate pace//Cycling - 20 minutes at a vigorous pace//Russian Twists - 4 sets of 15 reps each side//Leg Raises - 4 sets of 12 reps'
            tue = 'Day 2: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            wed = 'Day 3: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            thu = 'Day 6: Active RecoveryYoga - 60 minutes focusing on flexibility and core//Light Walking - 30 minutes at a gentle pace'
            fri = "Day 4: High-Intensity Interval Training (HIIT)//Sprints - 10 rounds of 30 seconds sprint/30 seconds rest//Burpees - 5 sets of 20 seconds on/40 seconds rest//Jump Rope - 10 minutes with intervals of 1 minute on/1 minute off"
            sat = 'Day 5: Full Body Strength//Squats - 4 sets of 10-12 reps//Bench Press - 4 sets of 10-12 reps//Deadlifts - 3 sets of 10 reps//Pull-ups - 3 sets of AMRAP//Plank - 3 sets of 1 min hold'
            sun = 'rest'

    elif member.fitness_goal == 'improve_endurance':
        if member.act_levels == '1-3 x times a week':
            mon = "Day 1: Cardio Intervals//Treadmill or Outdoor Running - 30 minutes of interval training (1 min fast/2 min slow)"
            tue = "rest"
            wed = "Day 2: Full Body Circuit//Bodyweight Exercises (Push-ups, Pull-ups, Squats) - 3 rounds of 15 reps each"
            thu = "rest"
            fri = "Day 3: Long Duration Cardio//Cycling or Swimming - 45 minutes at a steady pace"
            sat = "rest"
            sun = "rest"

        elif member.act_levels == '3-5 x times a week':
            mon = "Day 1: High Intensity Interval Training//HIIT - 20 minutes (30s high intensity/30s low intensity)"
            tue = "rest"
            wed = "Day 2: Strength and Endurance Circuit//Mix of Weight Lifting and Bodyweight Exercises - 3 sets of 12 reps"
            thu = "Day 3: Cardio Intervals//Rowing Machine or Jump Rope - 20 minutes of interval training"
            fri = "rest"
            sat = "Day 4: Long Duration Cardio//Jogging - 60 minutes at a moderate pace"
            sun = "rest"

        elif member.act_levels == '5-6 x times a week':
            mon = "Day 1: Cardio Intervals//Treadmill Sprints - 30 minutes of interval training (1 min sprint/2 min walk)"
            tue = "Day 2: Circuit Training//Full body circuit with resistance bands - 3 circuits of 10 mins each"
            wed = "rest"
            thu = "Day 3: Strength Training//Bodyweight strength exercises - 4 sets of 10-12 reps"
            fri = "Day 4: Cardio Endurance//Steady State Cycling - 50 minutes at a moderate intensity"
            sat = "Day 5: Active Recovery//Yoga or light stretching - 30 minutes"
            sun = "rest"

        elif member.act_levels == '6-7 x times a week':
            mon = "Day 1: Interval Training//Treadmill intervals - 25 minutes (3 min run/2 min walk)"
            tue = "Day 2: Circuit Training//Kettlebell circuit - 4 sets of 15 reps"
            wed = "Day 3: Endurance Cardio//Long distance running - 60 minutes at a steady pace"
            thu = "Day 4: High-Intensity Bodyweight//Tabata style - 20 minutes (20s work/10s rest)"
            fri = "Day 5: Strength Focus//Compound lifting - Squats, Deadlifts, Bench Press - 3 sets of 8-12 reps"
            sat = "Day 6: Mixed Cardio//Rowing and Cycling - 45 minutes total"
            sun = "Day 7: Active Rest//Stretching and foam rolling - 30 minutes"

    if member.fitness_goal == 'increase_flexibility':
        if member.act_levels == '1-3 x times a week':
            mon = "Day 1: Yoga Stretching//Full body yoga - 30 minutes"
            tue = "rest"
            wed = "Day 2: Dynamic Stretching//Full body dynamic stretches - 20 minutes"
            thu = "rest"
            fri = "Day 3: Pilates//Beginner Pilates session - 30 minutes"
            sat = "rest"
            sun = "rest"

        elif member.act_levels == '3-5 x times a week':
            mon = "Day 1: Yoga Stretching//Full body yoga - 45 minutes"
            tue = "rest"
            wed = "Day 2: Dynamic Stretching//Leg and hip dynamic stretches - 20 minutes"
            thu = "Day 3: Tai Chi//Beginner Tai Chi class - 30 minutes"
            fri = "rest"
            sat = "Day 4: Pilates//Intermediate Pilates session - 40 minutes"
            sun = "rest"

        elif member.act_levels == '5-6 x times a week':
            mon = "Day 1: Yoga Stretching//Advanced yoga poses - 45 minutes"
            tue = "Day 2: Pilates//Core-focused Pilates - 40 minutes"
            wed = "rest"
            thu = "Day 3: Dynamic Stretching//Full body dynamic stretches - 30 minutes"
            fri = "Day 4: Tai Chi//Intermediate Tai Chi session - 45 minutes"
            sat = "Day 5: Active Recovery//Light yoga and meditation - 30 minutes"
            sun = "rest"

        elif member.act_levels == '6-7 x times a week':
            mon = "Day 1: Yoga Stretching//Intensive yoga session - 60 minutes"
            tue = "Day 2: Dynamic Stretching//Sports specific stretches - 30 minutes"
            wed = "Day 3: Pilates//Advanced Pilates session - 45 minutes"
            thu = "Day 4: Yoga Stretching//Power yoga - 45 minutes"
            fri = "Day 5: Tai Chi//Advanced Tai Chi practice - 60 minutes"
            sat = "Day 6: Dynamic Stretching//Injury prevention stretches - 30 minutes"
            sun = "Day 7: Active Rest//Gentle yoga and deep breathing - 30 minutes"

    #namem position
    name_pos = member.name

    #achievements
    bmi_good = ''
    bp_normal = ''
    if bp_health =='Normal':
        bp_normal = '🥇Achieved a healthy Blood pressure'

    if bmi_category == 'Healthy ✅':
        bmi_good = '🥇Healthy BMI'

    if bmr!=100:
        bmr_achieve = '🥇You have found your BMR'

    lose=''
    gain = ''
    flex=''
    run=''

    if member.fitness_goal == 'lose_weight':
        lose = '🥇You are losing weight'
    elif member.fitness_goal == 'gain_muscle':
        gain = '🥇You are gaining muscle'
    elif member.fitness_goal == 'improve_endurance':
        run = '🥇 Your endurance is improving'
    elif member.fitness_goal=='increase_flexibility':
        flex='🥇 Getting more flexible'
    
    context['member'] = member
    context['bmi'] = bmi
    context['bmi_category'] = bmi_category
    context['bp_health'] = bp_health
    context['bp'] = bp
    context['bmr'] = bmr
    context['rec_bmr'] = rec_bmr
    context['mon'] = mon
    context['tue'] = tue
    context['wed'] = wed
    context['thu'] = thu
    context['fri'] = fri
    context['sat'] = sat
    context['sun'] = sun
    context['name_pos'] = name_pos
    context['bmi_good'] = bmi_good
    context['bp_normal'] = bp_normal
    context['bmr_achieve'] = bmr_achieve
    context['lose'] = lose
    context['gain'] = gain
    context['run'] = run
    context['flex'] = flex

    return render(request, 'myapp/profile/index.html', context)

def member_login(request):
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        password = request.POST.get('password').strip()
        try:
            member = Member.objects.get(name=name, password=password)
        except Member.DoesNotExist:
            return render(request, 'myapp/login/memberLogin.html', {'error': 'Invalid username or password'})
        request.session['member_id'] = member.member_id
        return redirect('dashboard')
    else:
        return render(request, 'myapp/login/memberLogin.html')
    
    

