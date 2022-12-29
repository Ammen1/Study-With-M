
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout

from base.EmailBackEnd import EmailBackEnd
from .models import Room, Students, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm
from django.shortcuts import render, redirect
from django.http import HttpResponse,HttpResponseRedirect
from django.contrib import messages
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from studybud import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from . tokens import generate_token
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from studybud import settings


def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            user_type = user.user_type
            if user_type == '1':
                #return HttpResponse("admin Login")
                return redirect('admin_home')
            elif user_type == '2':
                return redirect('staff_home')
            elif user_type == '3':
                return redirect('home')   
            else:
                messages.error(request, "Invalid Login!")
                return redirect('home')

        else:
            messages.error(request, "Invalid Login Credentials!")
            #return HttpResponseRedirect("/")
            return redirect('home')

    context = {'page': page}
    return render(request, 'base/login_register.html', context)

def get_user_details(request):
    if request.user != None:
        return HttpResponse("User: "+request.user.email+" User Type: "+request.user.user_type)
    else:
        return HttpResponse("Please Login First")


def logout_User(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    form = MyUserCreationForm()
    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.is_active = False
            user.save()
            login(request, user)
            messages.success(request, "Your Account has been created succesfully!! Please check your email to confirm your email address in order to activate your account.")

            # Welcome Email
            subject = "Welcome to Debo E-learning!!"
            message = "Hello " + str(user.name) + "!! \n" + "Welcome to Debo E-learning\nThank you for visiting our website\n. We have also sent you a confirmation email, please confirm your email address. \n\nThanking You"        
            from_email = settings.EMAIL_HOST_USER
            to_list = [user.email]
            send_mail(subject, message, from_email, to_list, fail_silently=True)


            # Email Address Confirmation Email
            current_site = get_current_site(request)
            email_subject = "Confirm your Email @ Debo E-learneing!!"
            message2 = render_to_string('email_confirmation.html',{
                'name': user.name,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': generate_token.make_token(user)
                })

            email = EmailMessage(
                email_subject,
                message2,
                settings.EMAIL_HOST_USER,
                [user.email],
                )
            email.fail_silently = True
            email.send()
            return redirect('home')
               
        else:
            messages.error(request, 'An error occurred during registration')

    return render(request, 'base/login_register.html', {'form': form})

                
def activate(request,uidb64,token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError,ValueError,OverflowError,User.DoesNotExist):
        user = None

    if user is not None and generate_token.check_token(user,token):
        user.is_active = True
        user.save()
        login(request,user)
        messages.success(request, "Your Account has been activated!!")
        return redirect('home')
    else:
        return render(request,'activation_failed.html')

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(
        Q(room__topic__name__icontains=q))[0:3]

    context = {'rooms': rooms, 'topics': topics,
               'room_count': room_count, 'room_messages': room_messages}
    return render(request, 'base/home.html', context)

@login_required(login_url='login')
def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()

    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages,
               'participants': participants}
    return render(request, 'base/room.html', context)


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms,
               'room_messages': room_messages, 'topics': topics}
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    if request.user != room.host:
        return HttpResponse('Your are not allowed here!!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')

    context = {'form': form, 'topics': topics, 'room': room}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('Your are not allowed here!!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('Your are not allowed here!!')

    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': message})


@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    return render(request, 'base/update-user.html', {'form': form})


def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {'topics': topics})


def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages': room_messages})




# @login_required(login_url='login')
# def admin_home(request):
#     all_student_count = Students.objects.all().count()
#     subject_count = Subjects.objects.all().count()
#     course_count = Courses.objects.all().count()
#     staff_count = Staffs.objects.all().count()

#     # Total Subjects and students in Each Course
#     course_all = Courses.objects.all()
#     course_name_list = []
#     subject_count_list = []
#     student_count_list_in_course = []

#     for course in course_all:
#         subjects = Subjects.objects.filter(course_id=course.id).count()
#         students = Students.objects.filter(course_id=course.id).count()
#         course_name_list.append(course.course_name)
#         subject_count_list.append(subjects)
#         student_count_list_in_course.append(students)
    
#     subject_all = Subjects.objects.all()
#     subject_list = []
#     student_count_list_in_subject = []
#     for subject in subject_all:
#         course = Courses.objects.get(id=subject.course_id.id)
#         student_count = Students.objects.filter(course_id=course.id).count()
#         subject_list.append(subject.subject_name)
#         student_count_list_in_subject.append(student_count)
    
#     # For Saffs
#     staff_attendance_present_list=[]
#     staff_attendance_leave_list=[]
#     staff_name_list=[]

#     staffs = Staffs.objects.all()
#     for staff in staffs:
#         subject_ids = Subjects.objects.filter(staff_id=staff.admin.id)
#         attendance = Attendance.objects.filter(subject_id__in=subject_ids).count()
#         leaves = LeaveReportStaff.objects.filter(staff_id=staff.id, leave_status=1).count()
#         staff_attendance_present_list.append(attendance)
#         staff_attendance_leave_list.append(leaves)
#         staff_name_list.append(staff.admin.first_name)

#     # For Students
#     student_attendance_present_list=[]
#     student_attendance_leave_list=[]
#     student_name_list=[]

#     students = Students.objects.all()
#     for student in students:
#         attendance = AttendanceReport.objects.filter(student_id=student.id, status=True).count()
#         absent = AttendanceReport.objects.filter(student_id=student.id, status=False).count()
#         leaves = LeaveReportStudent.objects.filter(student_id=student.id, leave_status=1).count()
#         student_attendance_present_list.append(attendance)
#         student_attendance_leave_list.append(leaves+absent)
#         student_name_list.append(student.admin.first_name)


#     context={
#         "all_student_count": all_student_count,
#         "subject_count": subject_count,
#         "course_count": course_count,
#         "staff_count": staff_count,
#         "course_name_list": course_name_list,
#         "subject_count_list": subject_count_list,
#         "student_count_list_in_course": student_count_list_in_course,
#         "subject_list": subject_list,
#         "student_count_list_in_subject": student_count_list_in_subject,
#         "staff_attendance_present_list": staff_attendance_present_list,
#         "staff_attendance_leave_list": staff_attendance_leave_list,
#         "staff_name_list": staff_name_list,
#         "student_attendance_present_list": student_attendance_present_list,
#         "student_attendance_leave_list": student_attendance_leave_list,
#         "student_name_list": student_name_list,
#     }
#     return render(request, "hod_template/home_content.html", context)


# def add_staff(request):
#     return render(request, "hod_template/add_staff_template.html")


# def add_staff_save(request):
#     if request.method != "POST":
#         messages.error(request, "Invalid Method ")
#         return redirect('add_staff')
#     else:
#         first_name = request.POST.get('first_name')
#         last_name = request.POST.get('last_name')
#         username = request.POST.get('username')
#         email = request.POST.get('email')
#         password = request.POST.get('password')
#         address = request.POST.get('address')

#         try:
#             user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name, user_type=2)
#             user.staffs.address = address
#             user.save()
#             messages.success(request, "Staff Added Successfully!")
#             return redirect('add_staff')
#         except:
#             messages.error(request, "Failed to Add Staff!")
#             return redirect('add_staff')



# def manage_staff(request):
#     staffs = Staffs.objects.all()
#     context = {
#         "staffs": staffs
#     }
#     return render(request, "hod_template/manage_staff_template.html", context)


# def edit_staff(request, staff_id):
#     staff = Staffs.objects.get(admin=staff_id)

#     context = {
#         "staff": staff,
#         "id": staff_id
#     }
#     return render(request, "hod_template/edit_staff_template.html", context)


# def edit_staff_save(request):
#     if request.method != "POST":
#         return HttpResponse("<h2>Method Not Allowed</h2>")
#     else:
#         staff_id = request.POST.get('staff_id')
#         username = request.POST.get('username')
#         email = request.POST.get('email')
#         first_name = request.POST.get('first_name')
#         last_name = request.POST.get('last_name')
#         address = request.POST.get('address')

#         try:
#             # INSERTING into Customuser Model
#             user = User.objects.get(id=staff_id)
#             user.first_name = first_name
#             user.last_name = last_name
#             user.email = email
#             user.username = username
#             user.save()
            
#             # INSERTING into Staff Model
#             staff_model = Staffs.objects.get(admin=staff_id)
#             staff_model.address = address
#             staff_model.save()

#             messages.success(request, "Staff Updated Successfully.")
#             return redirect('/edit_staff/'+staff_id)

#         except:
#             messages.error(request, "Failed to Update Staff.")
#             return redirect('/edit_staff/'+staff_id)



# def delete_staff(request, staff_id):
#     staff = Staffs.objects.get(admin=staff_id)
#     try:
#         staff.delete()
#         messages.success(request, "Staff Deleted Successfully.")
#         return redirect('manage_staff')
#     except:
#         messages.error(request, "Failed to Delete Staff.")
#         return redirect('manage_staff')




# def add_course(request):
#     return render(request, "hod_template/add_course_template.html")


# def add_course_save(request):
#     if request.method != "POST":
#         messages.error(request, "Invalid Method!")
#         return redirect('add_course')
#     else:
#         course = request.POST.get('course')
#         try:
#             course_model = Courses(course_name=course)
#             course_model.save()
#             messages.success(request, "Course Added Successfully!")
#             return redirect('add_course')
#         except:
#             messages.error(request, "Failed to Add Course!")
#             return redirect('add_course')


# def manage_course(request):
#     courses = Courses.objects.all()
#     context = {
#         "courses": courses
#     }
#     return render(request, 'hod_template/manage_course_template.html', context)


# def edit_course(request, course_id):
#     course = Courses.objects.get(id=course_id)
#     context = {
#         "course": course,
#         "id": course_id
#     }
#     return render(request, 'hod_template/edit_course_template.html', context)


# def edit_course_save(request):
#     if request.method != "POST":
#         HttpResponse("Invalid Method")
#     else:
#         course_id = request.POST.get('course_id')
#         course_name = request.POST.get('course')

#         try:
#             course = Courses.objects.get(id=course_id)
#             course.course_name = course_name
#             course.save()

#             messages.success(request, "Course Updated Successfully.")
#             return redirect('/edit_course/'+course_id)

#         except:
#             messages.error(request, "Failed to Update Course.")
#             return redirect('/edit_course/'+course_id)


# def delete_course(request, course_id):
#     course = Courses.objects.get(id=course_id)
#     try:
#         course.delete()
#         messages.success(request, "Course Deleted Successfully.")
#         return redirect('manage_course')
#     except:
#         messages.error(request, "Failed to Delete Course.")
#         return redirect('manage_course')


# def manage_session(request):
#     session_years = SessionYearModel.objects.all()
#     context = {
#         "session_years": session_years
#     }
#     return render(request, "hod_template/manage_session_template.html", context)


# def add_session(request):
#     return render(request, "hod_template/add_session_template.html")


# def add_session_save(request):
#     if request.method != "POST":
#         messages.error(request, "Invalid Method")
#         return redirect('add_course')
#     else:
#         session_start_year = request.POST.get('session_start_year')
#         session_end_year = request.POST.get('session_end_year')

#         try:
#             sessionyear = SessionYearModel(session_start_year=session_start_year, session_end_year=session_end_year)
#             sessionyear.save()
#             messages.success(request, "Session Year added Successfully!")
#             return redirect("add_session")
#         except:
#             messages.error(request, "Failed to Add Session Year")
#             return redirect("add_session")


# def edit_session(request, session_id):
#     session_year = SessionYearModel.objects.get(id=session_id)
#     context = {
#         "session_year": session_year
#     }
#     return render(request, "hod_template/edit_session_template.html", context)


# def edit_session_save(request):
#     if request.method != "POST":
#         messages.error(request, "Invalid Method!")
#         return redirect('manage_session')
#     else:
#         session_id = request.POST.get('session_id')
#         session_start_year = request.POST.get('session_start_year')
#         session_end_year = request.POST.get('session_end_year')

#         try:
#             session_year = SessionYearModel.objects.get(id=session_id)
#             session_year.session_start_year = session_start_year
#             session_year.session_end_year = session_end_year
#             session_year.save()

#             messages.success(request, "Session Year Updated Successfully.")
#             return redirect('/edit_session/'+session_id)
#         except:
#             messages.error(request, "Failed to Update Session Year.")
#             return redirect('/edit_session/'+session_id)


# def delete_session(request, session_id):
#     session = SessionYearModel.objects.get(id=session_id)
#     try:
#         session.delete()
#         messages.success(request, "Session Deleted Successfully.")
#         return redirect('manage_session')
#     except:
#         messages.error(request, "Failed to Delete Session.")
#         return redirect('manage_session')


# def add_student(request):
#     form = AddStudentForm()
#     context = {
#         "form": form
#     }
#     return render(request, 'hod_template/add_student_template.html', context)




# def add_student_save(request):
#     if request.method != "POST":
#         messages.error(request, "Invalid Method")
#         return redirect('add_student')
#     else:
#         form = AddStudentForm(request.POST, request.FILES)

#         if form.is_valid():
#             first_name = form.cleaned_data['first_name']
#             last_name = form.cleaned_data['last_name']
#             username = form.cleaned_data['username']
#             email = form.cleaned_data['email']
#             password = form.cleaned_data['password']
#             address = form.cleaned_data['address']
#             session_year_id = form.cleaned_data['session_year_id']
#             course_id = form.cleaned_data['course_id']
#             gender = form.cleaned_data['gender']

#             # Getting Profile Pic first
#             # First Check whether the file is selected or not
#             # Upload only if file is selected
#             if len(request.FILES) != 0:
#                 profile_pic = request.FILES['profile_pic']
#                 fs = FileSystemStorage()
#                 filename = fs.save(profile_pic.name, profile_pic)
#                 profile_pic_url = fs.url(filename)
#             else:
#                 profile_pic_url = None


#             try:
#                 user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name, user_type=3)
#                 user.students.address = address

#                 course_obj = Courses.objects.get(id=course_id)
#                 user.students.course_id = course_obj

#                 session_year_obj = SessionYearModel.objects.get(id=session_year_id)
#                 user.students.session_year_id = session_year_obj

#                 user.students.gender = gender
#                 user.students.profile_pic = profile_pic_url
#                 user.save()
#                 messages.success(request, "Student Added Successfully!")
#                 return redirect('add_student')
#             except:
#                 messages.error(request, "Failed to Add Student!")
#                 return redirect('add_student')
#         else:
#             return redirect('add_student')


# def manage_student(request):
#     students = Students.objects.all()
#     context = {
#         "students": students
#     }
#     return render(request, 'hod_template/manage_student_template.html', context)


# def edit_student(request, student_id):
#     # Adding Student ID into Session Variable
#     request.session['student_id'] = student_id

#     student = Students.objects.get(admin=student_id)
#     form = EditStudentForm()
#     # Filling the form with Data from Database
#     form.fields['email'].initial = student.admin.email
#     form.fields['username'].initial = student.admin.username
#     form.fields['first_name'].initial = student.admin.first_name
#     form.fields['last_name'].initial = student.admin.last_name
#     form.fields['address'].initial = student.address
#     form.fields['course_id'].initial = student.course_id.id
#     form.fields['gender'].initial = student.gender
#     form.fields['session_year_id'].initial = student.session_year_id.id

#     context = {
#         "id": student_id,
#         "username": student.admin.username,
#         "form": form
#     }
#     return render(request, "hod_template/edit_student_template.html", context)


# def edit_student_save(request):
#     if request.method != "POST":
#         return HttpResponse("Invalid Method!")
#     else:
#         student_id = request.session.get('student_id')
#         if student_id == None:
#             return redirect('/manage_student')

#         form = EditStudentForm(request.POST, request.FILES)
#         if form.is_valid():
#             email = form.cleaned_data['email']
#             username = form.cleaned_data['username']
#             first_name = form.cleaned_data['first_name']
#             last_name = form.cleaned_data['last_name']
#             address = form.cleaned_data['address']
#             course_id = form.cleaned_data['course_id']
#             gender = form.cleaned_data['gender']
#             session_year_id = form.cleaned_data['session_year_id']

#             # Getting Profile Pic first
#             # First Check whether the file is selected or not
#             # Upload only if file is selected
#             if len(request.FILES) != 0:
#                 profile_pic = request.FILES['profile_pic']
#                 fs = FileSystemStorage()
#                 filename = fs.save(profile_pic.name, profile_pic)
#                 profile_pic_url = fs.url(filename)
#             else:
#                 profile_pic_url = None

#             try:
#                 # First Update into Custom User Model
#                 user = User.objects.get(id=student_id)
#                 user.first_name = first_name
#                 user.last_name = last_name
#                 user.email = email
#                 user.username = username
#                 user.save()

#                 # Then Update Students Table
#                 student_model = Students.objects.get(admin=student_id)
#                 student_model.address = address

#                 course = Courses.objects.get(id=course_id)
#                 student_model.course_id = course

#                 session_year_obj = SessionYearModel.objects.get(id=session_year_id)
#                 student_model.session_year_id = session_year_obj

#                 student_model.gender = gender
#                 if profile_pic_url != None:
#                     student_model.profile_pic = profile_pic_url
#                 student_model.save()
#                 # Delete student_id SESSION after the data is updated
#                 del request.session['student_id']

#                 messages.success(request, "Student Updated Successfully!")
#                 return redirect('/edit_student/'+student_id)
#             except:
#                 messages.success(request, "Failed to Uupdate Student.")
#                 return redirect('/edit_student/'+student_id)
#         else:
#             return redirect('/edit_student/'+student_id)


# def delete_student(request, student_id):
#     student = Students.objects.get(admin=student_id)
#     try:
#         student.delete()
#         messages.success(request, "Student Deleted Successfully.")
#         return redirect('manage_student')
#     except:
#         messages.error(request, "Failed to Delete Student.")
#         return redirect('manage_student')


# def add_subject(request):
#     courses = Courses.objects.all()
#     staffs =User.objects.filter(user_type='2')
#     context = {
#         "courses": courses,
#         "staffs": staffs
#     }
#     return render(request, 'hod_template/add_subject_template.html', context)



# def add_subject_save(request):
#     if request.method != "POST":
#         messages.error(request, "Method Not Allowed!")
#         return redirect('add_subject')
#     else:
#         subject_name = request.POST.get('subject')

#         course_id = request.POST.get('course')
#         course = Courses.objects.get(id=course_id)
        
#         staff_id = request.POST.get('staff')
#         staff = User.objects.get(id=staff_id)

#         try:
#             subject = Subjects(subject_name=subject_name, course_id=course, staff_id=staff)
#             subject.save()
#             messages.success(request, "Subject Added Successfully!")
#             return redirect('add_subject')
#         except:
#             messages.error(request, "Failed to Add Subject!")
#             return redirect('add_subject')


# def manage_subject(request):
#     subjects = Subjects.objects.all()
#     context = {
#         "subjects": subjects
#     }
#     return render(request, 'hod_template/manage_subject_template.html', context)


# def edit_subject(request, subject_id):
#     subject = Subjects.objects.get(id=subject_id)
#     courses = Courses.objects.all()
#     staffs = User.objects.filter(user_type='2')
#     context = {
#         "subject": subject,
#         "courses": courses,
#         "staffs": staffs,
#         "id": subject_id
#     }
#     return render(request, 'hod_template/edit_subject_template.html', context)


# def edit_subject_save(request):
#     if request.method != "POST":
#         HttpResponse("Invalid Method.")
#     else:
#         subject_id = request.POST.get('subject_id')
#         subject_name = request.POST.get('subject')
#         course_id = request.POST.get('course')
#         staff_id = request.POST.get('staff')

#         try:
#             subject = Subjects.objects.get(id=subject_id)
#             subject.subject_name = subject_name

#             course = Courses.objects.get(id=course_id)
#             subject.course_id = course

#             staff = User.objects.get(id=staff_id)
#             subject.staff_id = staff
            
#             subject.save()

#             messages.success(request, "Subject Updated Successfully.")
#             # return redirect('/edit_subject/'+subject_id)
#             return HttpResponseRedirect(reverse("edit_subject", kwargs={"subject_id":subject_id}))

#         except:
#             messages.error(request, "Failed to Update Subject.")
#             return HttpResponseRedirect(reverse("edit_subject", kwargs={"subject_id":subject_id}))
#             # return redirect('/edit_subject/'+subject_id)



# def delete_subject(request, subject_id):
#     subject = Subjects.objects.get(id=subject_id)
#     try:
#         subject.delete()
#         messages.success(request, "Subject Deleted Successfully.")
#         return redirect('manage_subject')
#     except:
#         messages.error(request, "Failed to Delete Subject.")
#         return redirect('manage_subject')


# @csrf_exempt
# def check_email_exist(request):
#     email = request.POST.get("email")
#     user_obj = User.objects.filter(email=email).exists()
#     if user_obj:
#         return HttpResponse(True)
#     else:
#         return HttpResponse(False)


# @csrf_exempt
# def check_username_exist(request):
#     username = request.POST.get("username")
#     user_obj = User.objects.filter(username=username).exists()
#     if user_obj:
#         return HttpResponse(True)
#     else:
#         return HttpResponse(False)



# def student_feedback_message(request):
#     feedbacks = FeedBackStudent.objects.all()
#     context = {
#         "feedbacks": feedbacks
#     }
#     return render(request, 'hod_template/student_feedback_template.html', context)


# @csrf_exempt
# def student_feedback_message_reply(request):
#     feedback_id = request.POST.get('id')
#     feedback_reply = request.POST.get('reply')

#     try:
#         feedback = FeedBackStudent.objects.get(id=feedback_id)
#         feedback.feedback_reply = feedback_reply
#         feedback.save()
#         return HttpResponse("True")

#     except:
#         return HttpResponse("False")


# def staff_feedback_message(request):
#     feedbacks = FeedBackStaffs.objects.all()
#     context = {
#         "feedbacks": feedbacks
#     }
#     return render(request, 'hod_template/staff_feedback_template.html', context)


# @csrf_exempt
# def staff_feedback_message_reply(request):
#     feedback_id = request.POST.get('id')
#     feedback_reply = request.POST.get('reply')

#     try:
#         feedback = FeedBackStaffs.objects.get(id=feedback_id)
#         feedback.feedback_reply = feedback_reply
#         feedback.save()
#         return HttpResponse("True")

#     except:
#         return HttpResponse("False")


# def student_leave_view(request):
#     leaves = LeaveReportStudent.objects.all()
#     context = {
#         "leaves": leaves
#     }
#     return render(request, 'hod_template/student_leave_view.html', context)

# def student_leave_approve(request, leave_id):
#     leave = LeaveReportStudent.objects.get(id=leave_id)
#     leave.leave_status = 1
#     leave.save()
#     return redirect('student_leave_view')


# def student_leave_reject(request, leave_id):
#     leave = LeaveReportStudent.objects.get(id=leave_id)
#     leave.leave_status = 2
#     leave.save()
#     return redirect('student_leave_view')


# def staff_leave_view(request):
#     leaves = LeaveReportStaff.objects.all()
#     context = {
#         "leaves": leaves
#     }
#     return render(request, 'hod_template/staff_leave_view.html', context)


# def staff_leave_approve(request, leave_id):
#     leave = LeaveReportStaff.objects.get(id=leave_id)
#     leave.leave_status = 1
#     leave.save()
#     return redirect('staff_leave_view')


# def staff_leave_reject(request, leave_id):
#     leave = LeaveReportStaff.objects.get(id=leave_id)
#     leave.leave_status = 2
#     leave.save()
#     return redirect('staff_leave_view')


# def admin_view_attendance(request):
#     subjects = Subjects.objects.all()
#     session_years = SessionYearModel.objects.all()
#     context = {
#         "subjects": subjects,
#         "session_years": session_years
#     }
#     return render(request, "hod_template/admin_view_attendance.html", context)


# @csrf_exempt
# def admin_get_attendance_dates(request):
#     # Getting Values from Ajax POST 'Fetch Student'
#     subject_id = request.POST.get("subject")
#     session_year = request.POST.get("session_year_id")

#     # Students enroll to Course, Course has Subjects
#     # Getting all data from subject model based on subject_id
#     subject_model = Subjects.objects.get(id=subject_id)

#     session_model = SessionYearModel.objects.get(id=session_year)

#     # students = Students.objects.filter(course_id=subject_model.course_id, session_year_id=session_model)
#     attendance = Attendance.objects.filter(subject_id=subject_model, session_year_id=session_model)

#     # Only Passing Student Id and Student Name Only
#     list_data = []

#     for attendance_single in attendance:
#         data_small={"id":attendance_single.id, "attendance_date":str(attendance_single.attendance_date), "session_year_id":attendance_single.session_year_id.id}
#         list_data.append(data_small)

#     return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)


# @csrf_exempt
# def admin_get_attendance_student(request):
#     # Getting Values from Ajax POST 'Fetch Student'
#     attendance_date = request.POST.get('attendance_date')
#     attendance = Attendance.objects.get(id=attendance_date)

#     attendance_data = AttendanceReport.objects.filter(attendance_id=attendance)
#     # Only Passing Student Id and Student Name Only
#     list_data = []

#     for student in attendance_data:
#         data_small={"id":student.student_id.admin.id, "name":student.student_id.admin.first_name+" "+student.student_id.admin.last_name, "status":student.status}
#         list_data.append(data_small)

#     return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)


# def admin_profile(request):
#     user = User.objects.get(id=request.user.id)

#     context={
#         "user": user
#     }
#     return render(request, 'hod_template/admin_profile.html', context)


# def admin_profile_update(request):
#     if request.method != "POST":
#         messages.error(request, "Invalid Method!")
#         return redirect('admin_profile')
#     else:
#         first_name = request.POST.get('first_name')
#         last_name = request.POST.get('last_name')
#         password = request.POST.get('password')

#         try:
#             customuser = User.objects.get(id=request.user.id)
#             customuser.first_name = first_name
#             customuser.last_name = last_name
#             if password != None and password != "":
#                 customuser.set_password(password)
#             customuser.save()
#             messages.success(request, "Profile Updated Successfully")
#             return redirect('admin_profile')
#         except:
#             messages.error(request, "Failed to Update Profile")
#             return redirect('admin_profile')
    


# def staff_profile(request):
#     pass


# def student_profile(requtest):
#     pass




