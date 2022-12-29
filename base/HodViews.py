from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.core.files.storage import FileSystemStorage #To upload Profile Picture
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
import json

from base.models import AdminHOD, User, Staffs, Courses, Subjects, Students, SessionYearModel, FeedBackStudent, FeedBackStaffs, LeaveReportStudent, LeaveReportStaff, Attendance, AttendanceReport
from .forms import AddStudentForm, EditStudentForm

@login_required(login_url='login')
@cache_control(no_data=True, must_revalidade=True, no_strore=True)
def admin_home(request):
    all_student_count = Students.objects.all().count()
    subject_count = Subjects.objects.all().count()
    course_count = Courses.objects.all().count()
    staff_count = Staffs.objects.all().count()
    admin_home = AdminHOD.objects.get(admin=request.user.id)

    # Total Subjects and students in Each Course
    course_all = Courses.objects.all()
    course_name_list = []
    subject_count_list = []
    student_count_list_in_course = []

    for course in course_all:
        subjects = Subjects.objects.filter(course_id=course.id).count()
        students = Students.objects.filter(course_id=course.id).count()
        course_name_list.append(course.course_name)
        subject_count_list.append(subjects)
        student_count_list_in_course.append(students)
    
    subject_all = Subjects.objects.all()
    subject_list = []
    student_count_list_in_subject = []
    for subject in subject_all:
        course = Courses.objects.get(id=subject.course_id.id)
        student_count = Students.objects.filter(course_id=course.id).count()
        subject_list.append(subject.subject_name)
        student_count_list_in_subject.append(student_count)
    
    # For Saffs
    staff_attendance_present_list=[]
    staff_attendance_leave_list=[]
    staff_name_list=[]

    staffs = Staffs.objects.all()
    for staff in staffs:
        subject_ids = Subjects.objects.filter(staff_id=staff.admin.id)
        attendance = Attendance.objects.filter(subject_id__in=subject_ids).count()
        leaves = LeaveReportStaff.objects.filter(staff_id=staff.id, leave_status=1).count()
        staff_attendance_present_list.append(attendance)
        staff_attendance_leave_list.append(leaves)
        staff_name_list.append(staff.admin.first_name)

    # For Students
    student_attendance_present_list=[]
    student_attendance_leave_list=[]
    student_name_list=[]

    students = Students.objects.all()
    for student in students:
        attendance = AttendanceReport.objects.filter(student_id=student.id, status=True).count()
        absent = AttendanceReport.objects.filter(student_id=student.id, status=False).count()
        leaves = LeaveReportStudent.objects.filter(student_id=student.id, leave_status=1).count()
        student_attendance_present_list.append(attendance)
        student_attendance_leave_list.append(leaves+absent)
        student_name_list.append(student.admin.first_name)


    context={
        "all_student_count": all_student_count,
        "subject_count": subject_count,
        "course_count": course_count,
        "staff_count": staff_count,
        "course_name_list": course_name_list,
        "subject_count_list": subject_count_list,
        "student_count_list_in_course": student_count_list_in_course,
        "subject_list": subject_list,
        "student_count_list_in_subject": student_count_list_in_subject,
        "staff_attendance_present_list": staff_attendance_present_list,
        "staff_attendance_leave_list": staff_attendance_leave_list,
        "staff_name_list": staff_name_list,
        "student_attendance_present_list": student_attendance_present_list,
        "student_attendance_leave_list": student_attendance_leave_list,
        "student_name_list": student_name_list,
    }
    return render(request, "hod_template/home_content.html", context)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def add_staff(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    return render(request, "hod_template/add_staff_template.html")

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def add_staff_save(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    if request.method != "POST":
        messages.error(request, "Invalid Method ")
        return redirect('add_staff')
    else:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        address = request.POST.get('address')

        try:
            user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name, user_type=2)
            user.staffs.address = address
            user.save()
            messages.success(request, "Staff Added Successfully!")
            return redirect('add_staff')
        except:
            messages.error(request, "Failed to Add Staff!")
            return redirect('add_staff')


@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def manage_staff(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    staffs = Staffs.objects.all()
    context = {
        "staffs": staffs
    }
    return render(request, "hod_template/manage_staff_template.html", context)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def edit_staff(request, staff_id):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    staff = Staffs.objects.get(admin=staff_id)

    context = {
        "staff": staff,
        "id": staff_id
    }
    return render(request, "hod_template/edit_staff_template.html", context)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def edit_staff_save(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    if request.method != "POST":
        return HttpResponse("<h2>Method Not Allowed</h2>")
    else:
        staff_id = request.POST.get('staff_id')
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')

        try:
            # INSERTING into user Model
            user = User.objects.get(id=staff_id)
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.username = username
            user.save()
            
            # INSERTING into Staff Model
            staff_model = Staffs.objects.get(admin=staff_id)
            staff_model.address = address
            staff_model.save()

            messages.success(request, "Staff Updated Successfully.")
            return redirect('/edit_staff/'+staff_id)

        except:
            messages.error(request, "Failed to Update Staff.")
            return redirect('/edit_staff/'+staff_id)


@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def delete_staff(request, staff_id):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    staff = Staffs.objects.get(admin=staff_id)
    try:
        staff.delete()
        messages.success(request, "Staff Deleted Successfully.")
        return redirect('manage_staff')
    except:
        messages.error(request, "Failed to Delete Staff.")
        return redirect('manage_staff')



@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def add_course(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    return render(request, "hod_template/add_course_template.html")

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def add_course_save(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    if request.method != "POST":
        messages.error(request, "Invalid Method!")
        return redirect('add_course')
    else:
        course = request.POST.get('course')
        try:
            course_model = Courses(course_name=course)
            course_model.save()
            messages.success(request, "Course Added Successfully!")
            return redirect('add_course')
        except:
            messages.error(request, "Failed to Add Course!")
            return redirect('add_course')

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def manage_course(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    courses = Courses.objects.all()
    context = {
        "courses": courses
    }
    return render(request, 'hod_template/manage_course_template.html', context)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def edit_course(request, course_id):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    course = Courses.objects.get(id=course_id)
    context = {
        "course": course,
        "id": course_id
    }
    return render(request, 'hod_template/edit_course_template.html', context)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def edit_course_save(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    if request.method != "POST":
        HttpResponse("Invalid Method")
    else:
        course_id = request.POST.get('course_id')
        course_name = request.POST.get('course')

        try:
            course = Courses.objects.get(id=course_id)
            course.course_name = course_name
            course.save()

            messages.success(request, "Course Updated Successfully.")
            return redirect('/edit_course/'+course_id)

        except:
            messages.error(request, "Failed to Update Course.")
            return redirect('/edit_course/'+course_id)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def delete_course(request, course_id):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    course = Courses.objects.get(id=course_id)
    try:
        course.delete()
        messages.success(request, "Course Deleted Successfully.")
        return redirect('manage_course')
    except:
        messages.error(request, "Failed to Delete Course.")
        return redirect('manage_course')

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def manage_session(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    session_years = SessionYearModel.objects.all()
    context = {
        "session_years": session_years
    }
    return render(request, "hod_template/manage_session_template.html", context)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def add_session(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    return render(request, "hod_template/add_session_template.html")

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def add_session_save(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    if request.method != "POST":
        messages.error(request, "Invalid Method")
        return redirect('add_course')
    else:
        session_start_year = request.POST.get('session_start_year')
        session_end_year = request.POST.get('session_end_year')

        try:
            sessionyear = SessionYearModel(session_start_year=session_start_year, session_end_year=session_end_year)
            sessionyear.save()
            messages.success(request, "Session Year added Successfully!")
            return redirect("add_session")
        except:
            messages.error(request, "Failed to Add Session Year")
            return redirect("add_session")

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def edit_session(request, session_id):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    session_year = SessionYearModel.objects.get(id=session_id)
    context = {
        "session_year": session_year
    }
    return render(request, "hod_template/edit_session_template.html", context)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def edit_session_save(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    if request.method != "POST":
        messages.error(request, "Invalid Method!")
        return redirect('manage_session')
    else:
        session_id = request.POST.get('session_id')
        session_start_year = request.POST.get('session_start_year')
        session_end_year = request.POST.get('session_end_year')

        try:
            session_year = SessionYearModel.objects.get(id=session_id)
            session_year.session_start_year = session_start_year
            session_year.session_end_year = session_end_year
            session_year.save()

            messages.success(request, "Session Year Updated Successfully.")
            return redirect('/edit_session/'+session_id)
        except:
            messages.error(request, "Failed to Update Session Year.")
            return redirect('/edit_session/'+session_id)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def delete_session(request, session_id):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    session = SessionYearModel.objects.get(id=session_id)
    try:
        session.delete()
        messages.success(request, "Session Deleted Successfully.")
        return redirect('manage_session')
    except:
        messages.error(request, "Failed to Delete Session.")
        return redirect('manage_session')

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def add_student(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    form = AddStudentForm()
    context = {
        "form": form
    }
    return render(request, 'hod_template/add_student_template.html', context)



@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def add_student_save(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    if request.method != "POST":
        messages.error(request, "Invalid Method")
        return redirect('add_student')
    else:
        form = AddStudentForm(request.POST, request.FILES)

        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            address = form.cleaned_data['address']
            session_year_id = form.cleaned_data['session_year_id']
            course_id = form.cleaned_data['course_id']
            gender = form.cleaned_data['gender']

            # Getting Profile Pic first
            # First Check whether the file is selected or not
            # Upload only if file is selected
            if len(request.FILES) != 0:
                profile_pic = request.FILES['profile_pic']
                fs = FileSystemStorage()
                filename = fs.save(profile_pic.name, profile_pic)
                profile_pic_url = fs.url(filename)
            else:
                profile_pic_url = None


            try:
                user = User.objects.create_user(username=username, password=password, email=email, first_name=first_name, last_name=last_name, user_type=3)
                user.students.address = address

                course_obj = Courses.objects.get(id=course_id)
                user.students.course_id = course_obj

                session_year_obj = SessionYearModel.objects.get(id=session_year_id)
                user.students.session_year_id = session_year_obj

                user.students.gender = gender
                user.students.profile_pic = profile_pic_url
                user.save()
                messages.success(request, "Student Added Successfully!")
                return redirect('add_student')
            except:
                messages.error(request, "Failed to Add Student!")
                return redirect('add_student')
        else:
            return redirect('add_student')

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def manage_student(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    students = Students.objects.all()
    context = {
        "students": students
    }
    return render(request, 'hod_template/manage_student_template.html', context)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
def edit_student(request, student_id):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    # Adding Student ID into Session Variable
    request.session['student_id'] = student_id

    student = Students.objects.get(admin=student_id)
    form = EditStudentForm()
    # Filling the form with Data from Database
    form.fields['email'].initial = student.admin.email
    form.fields['username'].initial = student.admin.username
    form.fields['first_name'].initial = student.admin.first_name
    form.fields['last_name'].initial = student.admin.last_name
    form.fields['address'].initial = student.address
    form.fields['course_id'].initial = student.course_id.id
    form.fields['gender'].initial = student.gender
    form.fields['session_year_id'].initial = student.session_year_id.id

    context = {
        "id": student_id,
        "username": student.admin.username,
        "form": form
    }
    return render(request, "hod_template/edit_student_template.html", context)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def edit_student_save(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    if request.method != "POST":
        return HttpResponse("Invalid Method!")
    else:
        student_id = request.session.get('student_id')
        if student_id == None:
            return redirect('/manage_student')

        form = EditStudentForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data['email']
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            address = form.cleaned_data['address']
            course_id = form.cleaned_data['course_id']
            gender = form.cleaned_data['gender']
            session_year_id = form.cleaned_data['session_year_id']

            # Getting Profile Pic first
            # First Check whether the file is selected or not
            # Upload only if file is selected
            if len(request.FILES) != 0:
                profile_pic = request.FILES['profile_pic']
                fs = FileSystemStorage()
                filename = fs.save(profile_pic.name, profile_pic)
                profile_pic_url = fs.url(filename)
            else:
                profile_pic_url = None

            try:
                # First Update into Custom User Model
                user = User.objects.get(id=student_id)
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.username = username
                user.save()

                # Then Update Students Table
                student_model = Students.objects.get(admin=student_id)
                student_model.address = address

                course = Courses.objects.get(id=course_id)
                student_model.course_id = course

                session_year_obj = SessionYearModel.objects.get(id=session_year_id)
                student_model.session_year_id = session_year_obj

                student_model.gender = gender
                if profile_pic_url != None:
                    student_model.profile_pic = profile_pic_url
                student_model.save()
                # Delete student_id SESSION after the data is updated
                del request.session['student_id']

                messages.success(request, "Student Updated Successfully!")
                return redirect('/edit_student/'+student_id)
            except:
                messages.success(request, "Failed to Uupdate Student.")
                return redirect('/edit_student/'+student_id)
        else:
            return redirect('/edit_student/'+student_id)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def delete_student(request, student_id):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    student = Students.objects.get(admin=student_id)
    try:
        student.delete()
        messages.success(request, "Student Deleted Successfully.")
        return redirect('manage_student')
    except:
        messages.error(request, "Failed to Delete Student.")
        return redirect('manage_student')

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def add_subject(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    courses = Courses.objects.all()
    staffs = User.objects.filter(user_type='2')
    context = {
        "courses": courses,
        "staffs": staffs
    }
    return render(request, 'hod_template/add_subject_template.html', context)


@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def add_subject_save(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    if request.method != "POST":
        messages.error(request, "Method Not Allowed!")
        return redirect('add_subject')
    else:
        subject_name = request.POST.get('subject')

        course_id = request.POST.get('course')
        course = Courses.objects.get(id=course_id)
        
        staff_id = request.POST.get('staff')
        staff = User.objects.get(id=staff_id)

        try:
            subject = Subjects(subject_name=subject_name, course_id=course, staff_id=staff)
            subject.save()
            messages.success(request, "Subject Added Successfully!")
            return redirect('add_subject')
        except:
            messages.error(request, "Failed to Add Subject!")
            return redirect('add_subject')

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def manage_subject(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    subjects = Subjects.objects.all()
    context = {
        "subjects": subjects
    }
    return render(request, 'hod_template/manage_subject_template.html', context)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def edit_subject(request, subject_id):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    subject = Subjects.objects.get(id=subject_id)
    courses = Courses.objects.all()
    staffs = User.objects.filter(user_type='2')
    context = {
        "subject": subject,
        "courses": courses,
        "staffs": staffs,
        "id": subject_id
    }
    return render(request, 'hod_template/edit_subject_template.html', context)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def edit_subject_save(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    if request.method != "POST":
        HttpResponse("Invalid Method.")
    else:
        subject_id = request.POST.get('subject_id')
        subject_name = request.POST.get('subject')
        course_id = request.POST.get('course')
        staff_id = request.POST.get('staff')

        try:
            subject = Subjects.objects.get(id=subject_id)
            subject.subject_name = subject_name

            course = Courses.objects.get(id=course_id)
            subject.course_id = course

            staff = User.objects.get(id=staff_id)
            subject.staff_id = staff
            
            subject.save()

            messages.success(request, "Subject Updated Successfully.")
            # return redirect('/edit_subject/'+subject_id)
            return HttpResponseRedirect(reverse("edit_subject", kwargs={"subject_id":subject_id}))

        except:
            messages.error(request, "Failed to Update Subject.")
            return HttpResponseRedirect(reverse("edit_subject", kwargs={"subject_id":subject_id}))
            # return redirect('/edit_subject/'+subject_id)


@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def delete_subject(request, subject_id):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    subject = Subjects.objects.get(id=subject_id)
    try:
        subject.delete()
        messages.success(request, "Subject Deleted Successfully.")
        return redirect('manage_subject')
    except:
        messages.error(request, "Failed to Delete Subject.")
        return redirect('manage_subject')


@csrf_exempt
@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def check_email_exist(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    email = request.POST.get("email")
    user_obj = User.objects.filter(email=email).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)


@csrf_exempt
@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def check_username_exist(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    username = request.POST.get("username")
    user_obj = User.objects.filter(username=username).exists()
    if user_obj:
        return HttpResponse(True)
    else:
        return HttpResponse(False)


@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def student_feedback_message(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    feedbacks = FeedBackStudent.objects.all()
    context = {
        "feedbacks": feedbacks
    }
    return render(request, 'hod_template/student_feedback_template.html', context)


@csrf_exempt
@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def student_feedback_message_reply(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    feedback_id = request.POST.get('id')
    feedback_reply = request.POST.get('reply')

    try:
        feedback = FeedBackStudent.objects.get(id=feedback_id)
        feedback.feedback_reply = feedback_reply
        feedback.save()
        return HttpResponse("True")

    except:
        return HttpResponse("False")

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def staff_feedback_message(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    feedbacks = FeedBackStaffs.objects.all()
    context = {
        "feedbacks": feedbacks
    }
    return render(request, 'hod_template/staff_feedback_template.html', context)


@csrf_exempt
@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def staff_feedback_message_reply(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    feedback_id = request.POST.get('id')
    feedback_reply = request.POST.get('reply')

    try:
        feedback = FeedBackStaffs.objects.get(id=feedback_id)
        feedback.feedback_reply = feedback_reply
        feedback.save()
        return HttpResponse("True")

    except:
        return HttpResponse("False")

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def student_leave_view(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    leaves = LeaveReportStudent.objects.all()
    context = {
        "leaves": leaves
    }
    return render(request, 'hod_template/student_leave_view.html', context)
@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def student_leave_approve(request, leave_id):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    leave = LeaveReportStudent.objects.get(id=leave_id)
    leave.leave_status = 1
    leave.save()
    return redirect('student_leave_view')

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def student_leave_reject(request, leave_id):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    leave = LeaveReportStudent.objects.get(id=leave_id)
    leave.leave_status = 2
    leave.save()
    return redirect('student_leave_view')

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def staff_leave_view(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    leaves = LeaveReportStaff.objects.all()
    context = {
        "leaves": leaves
    }
    return render(request, 'hod_template/staff_leave_view.html', context)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def staff_leave_approve(request, leave_id):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    leave = LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status = 1
    leave.save()
    return redirect('staff_leave_view')

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def staff_leave_reject(request, leave_id):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    leave = LeaveReportStaff.objects.get(id=leave_id)
    leave.leave_status = 2
    leave.save()
    return redirect('staff_leave_view')

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def admin_view_attendance(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    subjects = Subjects.objects.all()
    session_years = SessionYearModel.objects.all()
    context = {
        "subjects": subjects,
        "session_years": session_years
    }
    return render(request, "hod_template/admin_view_attendance.html", context)


@csrf_exempt
@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def admin_get_attendance_dates(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    # Getting Values from Ajax POST 'Fetch Student'
    subject_id = request.POST.get("subject")
    session_year = request.POST.get("session_year_id")

    # Students enroll to Course, Course has Subjects
    # Getting all data from subject model based on subject_id
    subject_model = Subjects.objects.get(id=subject_id)

    session_model = SessionYearModel.objects.get(id=session_year)

    # students = Students.objects.filter(course_id=subject_model.course_id, session_year_id=session_model)
    attendance = Attendance.objects.filter(subject_id=subject_model, session_year_id=session_model)

    # Only Passing Student Id and Student Name Only
    list_data = []

    for attendance_single in attendance:
        data_small={"id":attendance_single.id, "attendance_date":str(attendance_single.attendance_date), "session_year_id":attendance_single.session_year_id.id}
        list_data.append(data_small)

    return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)


@csrf_exempt
@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def admin_get_attendance_student(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    # Getting Values from Ajax POST 'Fetch Student'
    attendance_date = request.POST.get('attendance_date')
    attendance = Attendance.objects.get(id=attendance_date)

    attendance_data = AttendanceReport.objects.filter(attendance_id=attendance)
    # Only Passing Student Id and Student Name Only
    list_data = []

    for student in attendance_data:
        data_small={"id":student.student_id.admin.id, "name":student.student_id.admin.first_name+" "+student.student_id.admin.last_name, "status":student.status}
        list_data.append(data_small)

    return JsonResponse(json.dumps(list_data), content_type="application/json", safe=False)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def admin_profile(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    user = User.objects.get(id=request.user.id)

    context={
        "user": user
    }
    return render(request, 'hod_template/admin_profile.html', context)

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
@login_required(login_url='login')
def admin_profile_update(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    if request.method != "POST":
        messages.error(request, "Invalid Method!")
        return redirect('admin_profile')
    else:
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')

        try:
            customuser = User.objects.get(id=request.user.id)
            customuser.first_name = first_name
            customuser.last_name = last_name
            if password != None and password != "":
                customuser.set_password(password)
            customuser.save()
            messages.success(request, "Profile Updated Successfully")
            return redirect('admin_profile')
        except:
            messages.error(request, "Failed to Update Profile")
            return redirect('admin_profile')
    

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
def staff_profile(request):
    admin_home = AdminHOD.objects.get(admin=request.user.id)
    pass

@cache_control(no_data=True, must_revalidade=True, no_strore=True)
def student_profile(requtest):
    
    
    pass



