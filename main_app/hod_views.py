import json
import requests
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import  JsonResponse
from django.shortcuts import (HttpResponse,     HttpResponseRedirect,
                              get_object_or_404, redirect, render)
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView
from django.db.models import ProtectedError
from .forms import *
from .models import *


def admin_home(request):
    total_staff = Staff.objects.count()
    total_students = Student.objects.count()
    total_course = Course.objects.count()

    # Fanlar ro‘yxati
    all_subjects = Subject.objects.select_related('course').all()
    total_subject = all_subjects.count()

    # 1) Har bir fan bo‘yicha davomatlar soni (Attendance)
    attendance_list = []
    subject_short_list = []
    for subj in all_subjects:
        attendance_count = Attendance.objects.filter(subject=subj).count()
        subject_short_list.append(subj.name[:7])   # grafik uchun qisqa nom
        attendance_list.append(attendance_count)

    # 2) Har bir kurs bo‘yicha fanlar soni va talabalar soni
    course_name_list = []
    subject_count_list = []
    student_count_list_in_course = []
    all_courses = Course.objects.all()
    for course in all_courses:
        subj_count = Subject.objects.filter(course_id=course.id).count()
        stud_count = Student.objects.filter(course_id=course.id).count()
        course_name_list.append(course.name)
        subject_count_list.append(subj_count)
        student_count_list_in_course.append(stud_count)

    # 3) Har bir fan bo‘yicha (uning kursidagi) talabalar soni
    subject_name_list = []
    student_count_list_in_subject = []
    for subj in all_subjects:
        stud_count = Student.objects.filter(course_id=subj.course_id).count()
        subject_name_list.append(subj.name)
        student_count_list_in_subject.append(stud_count)


    student_attendance_present_list = []
    student_attendance_leave_list = []
    student_name_list = []

    all_students = Student.objects.select_related('admin').all()
    for s in all_students:
        present = AttendanceReport.objects.filter(student_id=s.id, status=True).count()
        absent = AttendanceReport.objects.filter(student_id=s.id, status=False).count()
        leave = LeaveReportStudent.objects.filter(student_id=s.id, status=1).count()

        student_attendance_present_list.append(present)
        student_attendance_leave_list.append(leave + absent)
        student_name_list.append(s.admin.first_name)

    context = {
        'page_title': "Administrator paneli",
        'total_students': total_students,
        'total_staff': total_staff,
        'total_course': total_course,
        'total_subject': total_subject,

        # grafiklar uchun
        'subject_list': subject_name_list,                 # fan nomlari (to‘liq)
        'attendance_list': attendance_list,                # davomatlar soni
        'course_name_list': course_name_list,              # kurs nomlari
        'student_count_list_in_course': student_count_list_in_course,
        'student_count_list_in_subject': student_count_list_in_subject,

        'student_attendance_present_list': student_attendance_present_list,
        'student_attendance_leave_list': student_attendance_leave_list,
        'student_name_list': student_name_list,
    }

    return render(request, 'hod_template/home_content.html', context)


def add_staff(request):
    form = StaffForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': "O‘qituvchi qo‘shish"}

    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            course = form.cleaned_data.get('course')

            passport = request.FILES.get('profile_pic')

            # ✅ Rasm majburiy bo‘lsa:
            if not passport:
                messages.error(request, "Profil rasmi kiritilmadi. Iltimos, rasm yuklang.")
                return render(request, 'hod_template/add_staff_template.html', context)

            fs = FileSystemStorage()
            filename = fs.save(passport.name, passport)
            passport_url = fs.url(filename)

            try:
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    user_type=2,
                    first_name=first_name,
                    last_name=last_name,
                    profile_pic=passport_url
                )
                user.gender = gender
                user.address = address
                user.staff.course = course
                user.save()

                messages.success(request, "O‘qituvchi muvaffaqiyatli qo‘shildi.")
                return redirect(reverse('add_staff'))

            except Exception as e:
                messages.error(request, "O‘qituvchini qo‘shib bo‘lmadi: " + str(e))
        else:
            messages.error(request, "Iltimos, formadagi barcha maydonlarni to‘g‘ri to‘ldiring.")

    return render(request, 'hod_template/add_staff_template.html', context)


def add_student(request):
    student_form = StudentForm(request.POST or None, request.FILES or None)
    context = {'form': student_form, 'page_title': "Talaba qo‘shish"}

    if request.method == 'POST':
        if student_form.is_valid():
            first_name = student_form.cleaned_data.get('first_name')
            last_name  = student_form.cleaned_data.get('last_name')
            address    = student_form.cleaned_data.get('address')
            email      = student_form.cleaned_data.get('email')
            gender     = student_form.cleaned_data.get('gender')
            password   = student_form.cleaned_data.get('password')
            course     = student_form.cleaned_data.get('course')
            session    = student_form.cleaned_data.get('session')

            passport = request.FILES.get('profile_pic')
            if not passport:
                messages.error(request, "Profil rasmi kiritilmadi. Iltimos, rasm yuklang.")
                return render(request, 'hod_template/add_student_template.html', context)

            fs = FileSystemStorage()
            filename = fs.save(passport.name, passport)
            passport_url = fs.url(filename)

            try:
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    user_type=3,
                    first_name=first_name,
                    last_name=last_name,
                    profile_pic=passport_url
                )
                user.gender = gender
                user.address = address

                # Student modeliga yozish
                user.student.session = session
                user.student.course = course
                user.save()

                messages.success(request, "Talaba muvaffaqiyatli qo‘shildi.")
                return redirect(reverse('add_student'))

            except Exception as e:
                messages.error(request, "Talabani qo‘shib bo‘lmadi: " + str(e))
        else:
            messages.error(request, "Iltimos, formadagi barcha maydonlarni to‘g‘ri to‘ldiring.")

    return render(request, 'hod_template/add_student_template.html', context)

def add_course(request):
    form = CourseForm(request.POST or None)
    context = {
        'form': form,
        'page_title': "Kurs qo‘shish"
    }

    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()   # ModelForm bo‘lsa eng to‘g‘ri usul
                messages.success(request, "Kurs muvaffaqiyatli qo‘shildi.")
                return redirect(reverse('add_course'))
            except Exception as e:
                messages.error(request, "Kursni qo‘shib bo‘lmadi: " + str(e))
        else:
            messages.error(request, "Iltimos, formani to‘g‘ri to‘ldiring.")

    return render(request, 'hod_template/add_course_template.html', context)


def add_subject(request):
    form = SubjectForm(request.POST or None)
    context = {
        'form': form,
        'page_title': "Fan qo‘shish"
    }

    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()  # ModelForm bo‘lsa shu yetarli
                messages.success(request, "Fan muvaffaqiyatli qo‘shildi.")
                return redirect(reverse('add_subject'))
            except Exception as e:
                messages.error(request, "Fanni qo‘shib bo‘lmadi: " + str(e))
        else:
            messages.error(request, "Iltimos, formani to‘g‘ri to‘ldiring.")

    return render(request, 'hod_template/add_subject_template.html', context)

def manage_staff(request):
    all_staff = CustomUser.objects.filter(user_type=2)

    context = {
        'allStaff': all_staff,
        'page_title': "O‘qituvchilarni boshqarish"
    }

    return render(request, "hod_template/manage_staff.html", context)


def manage_student(request):
    students = CustomUser.objects.filter(user_type=3)

    context = {
        'students': students,
        'page_title': "Talabalarni boshqarish"
    }

    return render(request, "hod_template/manage_student.html", context)


def manage_course(request):
    courses = Course.objects.all()

    context = {
        'courses': courses,
        'page_title': "Kurslarni boshqarish"
    }

    return render(request, "hod_template/manage_course.html", context)


def manage_subject(request):
    subjects = Subject.objects.all()

    context = {
        'subjects': subjects,
        'page_title': "Fanlarni boshqarish"
    }

    return render(request, "hod_template/manage_subject.html", context)


def edit_staff(request, staff_id):
    staff = get_object_or_404(Staff, id=staff_id)
    form = StaffForm(request.POST or None, request.FILES or None, instance=staff)

    context = {
        'form': form,
        'staff_id': staff_id,
        'page_title': "O‘qituvchini tahrirlash"
    }

    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            course = form.cleaned_data.get('course')
            passport = request.FILES.get('profile_pic')  # bo‘lmasa None bo‘ladi

            try:
                user = staff.admin

                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address

                # Parol faqat to‘ldirilsa yangilansin
                if password:
                    user.set_password(password)

                # Rasm faqat yuklansa yangilansin
                if passport:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    user.profile_pic = fs.url(filename)

                staff.course = course

                user.save()
                staff.save()

                messages.success(request, "Ma’lumotlar muvaffaqiyatli yangilandi.")
                return redirect(reverse('edit_staff', args=[staff_id]))

            except Exception as e:
                messages.error(request, "Yangilab bo‘lmadi: " + str(e))
        else:
            messages.error(request, "Iltimos, formani to‘g‘ri to‘ldiring.")

    # ✅ GET holatda ham shu return ishlaydi
    return render(request, "hod_template/edit_staff_template.html", context)

def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    form = StudentForm(request.POST or None, request.FILES or None, instance=student)

    context = {
        'form': form,
        'student_id': student_id,
        'page_title': "Talabani tahrirlash"
    }

    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name  = form.cleaned_data.get('last_name')
            address    = form.cleaned_data.get('address')
            email      = form.cleaned_data.get('email')
            gender     = form.cleaned_data.get('gender')
            password   = form.cleaned_data.get('password') or None
            course     = form.cleaned_data.get('course')
            session    = form.cleaned_data.get('session')
            passport   = request.FILES.get('profile_pic')  # bo‘lmasa None

            try:
                user = student.admin  # ✅ CustomUser

                # asosiy ma’lumotlar
                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address

                # parol faqat to‘ldirilsa yangilansin
                if password:
                    user.set_password(password)

                # rasm faqat yuklansa yangilansin
                if passport:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    user.profile_pic = fs.url(filename)

                # studentga tegishli maydonlar
                student.session = session
                student.course = course

                user.save()
                student.save()

                messages.success(request, "Ma’lumotlar muvaffaqiyatli yangilandi.")
                return redirect(reverse('edit_student', args=[student_id]))

            except Exception as e:
                messages.error(request, "Yangilab bo‘lmadi: " + str(e))
        else:
            messages.error(request, "Iltimos, formani to‘g‘ri to‘ldiring.")

    # ✅ GET ham, POST xato ham shu yerga keladi
    return render(request, "hod_template/edit_student_template.html", context)


def edit_course(request, course_id):
    instance = get_object_or_404(Course, id=course_id)
    form = CourseForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'course_id': course_id,
        'page_title': 'Edit Course'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                course = Course.objects.get(id=course_id)
                course.name = name
                course.save()
                messages.success(request, "Successfully Updated")
            except:
                messages.error(request, "Could Not Update")
        else:
            messages.error(request, "Could Not Update")

    return render(request, 'hod_template/edit_course_template.html', context)


def edit_subject(request, subject_id):
    instance = get_object_or_404(Subject, id=subject_id)
    form = SubjectForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'subject_id': subject_id,
        'page_title': 'Edit Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            course = form.cleaned_data.get('course')
            staff = form.cleaned_data.get('staff')
            try:
                subject = Subject.objects.get(id=subject_id)
                subject.name = name
                subject.staff = staff
                subject.course = course
                subject.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_subject', args=[subject_id]))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    return render(request, 'hod_template/edit_subject_template.html', context)


def add_session(request):
    form = SessionForm(request.POST or None)
    context = {'form': form, 'page_title': "O‘quv yilini qo‘shish"}

    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "O‘quv yili muvaffaqiyatli yaratildi.")
                return redirect(reverse('add_session'))
            except Exception as e:
                messages.error(request, "O‘quv yilini qo‘shib bo‘lmadi: " + str(e))
        else:
            messages.error(request, "Iltimos, formani to‘g‘ri to‘ldiring.")

    return render(request, "hod_template/add_session_template.html", context)

def manage_session(request):
    sessions = Session.objects.all()

    context = {
        'sessions': sessions,
        'page_title': "O‘quv yillarini boshqarish"
    }

    return render(request, "hod_template/manage_session.html", context)


def edit_session(request, session_id):
    instance = get_object_or_404(Session, id=session_id)
    form = SessionForm(request.POST or None, instance=instance)

    context = {
        'form': form,
        'session_id': session_id,
        'page_title': "O‘quv yilini tahrirlash"
    }

    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "O‘quv yili muvaffaqiyatli yangilandi.")
                return redirect(reverse('edit_session', args=[session_id]))
            except Exception as e:
                messages.error(request, "O‘quv yilini yangilab bo‘lmadi: " + str(e))
        else:
            messages.error(request, "Iltimos, formani to‘g‘ri to‘ldiring.")

    return render(request, "hod_template/edit_session_template.html", context)


@csrf_exempt
def check_email_availability(request):
    email = request.POST.get("email")

    if not email:
        return JsonResponse({
            "available": False,
            "message": "Email manzil kiritilmadi."
        })

    exists = CustomUser.objects.filter(email=email).exists()

    if exists:
        return JsonResponse({
            "available": False,
            "message": "Ushbu elektron pochta allaqachon ro‘yxatdan o‘tgan."
        })
    else:
        return JsonResponse({
            "available": True,
            "message": "Elektron pochta manzili mavjud."
        })


@csrf_exempt
def student_feedback_message(request):

    # GET — fikrlarni ko‘rsatish
    if request.method == 'GET':
        feedbacks = FeedbackStudent.objects.select_related('student__admin').all()

        context = {
            'feedbacks': feedbacks,
            'page_title': "Talabalar fikr-mulohazalari"
        }
        return render(request, 'hod_template/student_feedback_template.html', context)

    # POST — javob yozish
    feedback_id = request.POST.get('id')
    reply = request.POST.get('reply')

    if not feedback_id or not reply:
        return JsonResponse({
            "success": False,
            "message": "Ma’lumot to‘liq emas."
        })

    try:
        feedback = get_object_or_404(FeedbackStudent, id=feedback_id)
        feedback.reply = reply
        feedback.save()

        return JsonResponse({
            "success": True,
            "message": "Javob muvaffaqiyatli saqlandi."
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "Xatolik yuz berdi: " + str(e)
        })


@csrf_exempt
def staff_feedback_message(request):

    # GET — o‘qituvchilarning fikrlarini ko‘rsatish
    if request.method == 'GET':
        feedbacks = FeedbackStaff.objects.select_related('staff__admin').all()

        context = {
            'feedbacks': feedbacks,
            'page_title': "O‘qituvchilar fikr-mulohazalari"
        }
        return render(request, 'hod_template/staff_feedback_template.html', context)

    # POST — javob yozish
    feedback_id = request.POST.get('id')
    reply = request.POST.get('reply')

    if not feedback_id or not reply:
        return JsonResponse({
            "success": False,
            "message": "Ma’lumot to‘liq emas."
        })

    try:
        feedback = get_object_or_404(FeedbackStaff, id=feedback_id)
        feedback.reply = reply
        feedback.save()

        return JsonResponse({
            "success": True,
            "message": "Javob muvaffaqiyatli saqlandi."
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "Xatolik yuz berdi: " + str(e)
        })


@csrf_exempt
def view_staff_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportStaff.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Staff'
        }
        return render(request, "hod_template/staff_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportStaff, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False


@csrf_exempt
def view_student_leave(request):
    # GET — arizalar ro‘yxatini ko‘rsatish
    if request.method == 'GET':
        all_leave = LeaveReportStudent.objects.select_related('student__admin').all()

        context = {
            'allLeave': all_leave,
            'page_title': "Talabalardan ta’til arizalari"
        }
        return render(request, "hod_template/student_leave_view.html", context)

    # POST — ariza statusini o‘zgartirish (tasdiqlash/rad etish)
    leave_id = request.POST.get('id')
    status = request.POST.get('status')  # frontenddan '1' yoki boshqa qiymat keladi

    if not leave_id or not status:
        return JsonResponse({"success": False, "message": "Ma’lumot to‘liq emas."})

    # '1' => tasdiq, aks holda rad (sizdagi logika)
    new_status = 1 if str(status) == '1' else -1

    try:
        leave = get_object_or_404(LeaveReportStudent, id=leave_id)
        leave.status = new_status
        leave.save()

        return JsonResponse({
            "success": True,
            "message": "Ariza holati muvaffaqiyatli yangilandi."
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "Xatolik yuz berdi: " + str(e)
        })

def admin_view_attendance(request):
    subjects = Subject.objects.all()
    sessions = Session.objects.all()

    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': "Davomatni ko‘rish"
    }

    return render(request, "hod_template/admin_view_attendance.html", context)



@csrf_exempt
def get_admin_attendance(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    attendance_date_id = request.POST.get('attendance_date_id')

    if not subject_id or not session_id or not attendance_date_id:
        return JsonResponse({
            "success": False,
            "message": "Ma’lumotlar to‘liq emas."
        })

    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)

        attendance = get_object_or_404(
            Attendance,
            id=attendance_date_id,
            session=session,
            subject=subject
        )

        attendance_reports = AttendanceReport.objects.filter(
            attendance=attendance
        ).select_related('student__admin')

        data = []

        for report in attendance_reports:
            data.append({
                "student": report.student.admin.get_full_name(),
                "status": report.status  # True/False
            })

        return JsonResponse({
            "success": True,
            "data": data
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "Xatolik yuz berdi: " + str(e)
        })

def admin_view_profile(request):
    admin_obj = get_object_or_404(Admin, admin=request.user)
    form = AdminForm(request.POST or None, request.FILES or None, instance=admin_obj)

    context = {
        'form': form,
        'page_title': "Profil qo'shish"
    }

    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name  = form.cleaned_data.get('last_name')
            password   = form.cleaned_data.get('password') or None
            passport   = request.FILES.get('profile_pic')  # bo‘lmasa None

            try:
                user = admin_obj.admin  # CustomUser

                user.first_name = first_name
                user.last_name = last_name

                # Parol faqat kiritilsa yangilanadi
                if password:
                    user.set_password(password)

                # Rasm faqat yuklansa yangilanadi
                if passport:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    user.profile_pic = fs.url(filename)

                user.save()

                messages.success(request, "Profil muvaffaqiyatli yangilandi.")
                return redirect(reverse('admin_view_profile'))

            except Exception as e:
                messages.error(request, "Profilni yangilashda xatolik: " + str(e))
        else:
            messages.error(request, "Iltimos, formani to‘g‘ri to‘ldiring.")

    return render(request, "hod_template/admin_view_profile.html", context)

def admin_notify_staff(request):
    staff = CustomUser.objects.filter(user_type=2)

    context = {
        'page_title': "O‘qituvchilarga bildirishnoma yuborish",
        'allStaff': staff
    }

    return render(request, "hod_template/staff_notification.html", context)


def admin_notify_student(request):
    students = CustomUser.objects.filter(user_type=3)

    context = {
        'page_title': "Talabalarga bildirishnoma yuborish",
        'students': students
    }

    return render(request, "hod_template/student_notification.html", context)


@csrf_exempt
def send_student_notification(request):
    student_id = request.POST.get('id')
    message = request.POST.get('message')

    if not student_id or not message:
        return JsonResponse({
            "success": False,
            "message": "Ma’lumot to‘liq emas."
        })

    student = get_object_or_404(Student, admin_id=student_id)

    try:
        url = "https://fcm.googleapis.com/fcm/send"

        body = {
            'notification': {
                'title': "Ta’lim boshqaruv tizimi",
                'body': message,
                'click_action': reverse('student_view_notification'),
                'icon': static('dist/img/cmsl.png')
            },
            'to': student.admin.fcm_token
        }

        headers = {
            'Authorization': f'key={settings.FCM_SERVER_KEY}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, data=json.dumps(body), headers=headers)

        # Bazaga saqlash
        NotificationStudent.objects.create(
            student=student,
            message=message
        )

        return JsonResponse({
            "success": True,
            "message": "Bildirishnoma muvaffaqiyatli yuborildi."
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "Xatolik yuz berdi: " + str(e)
        })


@csrf_exempt
def send_staff_notification(request):
    staff_id = request.POST.get('id')
    message = request.POST.get('message')

    if not staff_id or not message:
        return JsonResponse({
            "success": False,
            "message": "Ma’lumot to‘liq emas."
        })

    staff = get_object_or_404(Staff, admin_id=staff_id)

    try:
        url = "https://fcm.googleapis.com/fcm/send"

        body = {
            'notification': {
                'title': "Ta’lim boshqaruv tizimi",
                'body': message,
                'click_action': reverse('staff_view_notification'),
                'icon': static('dist/img/cmsl.png')
            },
            'to': staff.admin.fcm_token
        }

        headers = {
            'Authorization': f'key={settings.FCM_SERVER_KEY}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, data=json.dumps(body), headers=headers)

        # Bildirishnomani bazaga saqlash
        NotificationStaff.objects.create(
            staff=staff,
            message=message
        )

        return JsonResponse({
            "success": True,
            "message": "Bildirishnoma muvaffaqiyatli yuborildi."
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "Xatolik yuz berdi: " + str(e)
        })


def delete_staff(request, staff_id):
    staff = get_object_or_404(CustomUser, staff__id=staff_id)

    try:
        staff.delete()
        messages.success(request, "O‘qituvchi muvaffaqiyatli o‘chirildi.")
    except ProtectedError:
        messages.error(
            request,
            "Bu o‘qituvchiga bog‘liq ma’lumotlar mavjud. "
            "Avval bog‘liq ma’lumotlarni o‘chiring."
        )
    except Exception as e:
        messages.error(request, "O‘qituvchini o‘chirib bo‘lmadi: " + str(e))

    return redirect(reverse('manage_staff'))

def delete_student(request, student_id):
    student = get_object_or_404(CustomUser, student__id=student_id)

    try:
        student.delete()
        messages.success(request, "Talaba muvaffaqiyatli o‘chirildi.")
    except ProtectedError:
        messages.error(
            request,
            "Bu talabaga bog‘liq ma’lumotlar mavjud. "
            "Avval ularni o‘chiring."
        )
    except Exception as e:
        messages.error(request, "Talabani o‘chirib bo‘lmadi: " + str(e))

    return redirect(reverse('manage_student'))


def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    try:
        course.delete()
        messages.success(request, "Kurs muvaffaqiyatli o‘chirildi.")
    except ProtectedError:
        messages.error(
            request,
            "Bu kursga biriktirilgan talabalar yoki fanlar mavjud. "
            "Avval ularni boshqa kursga o‘tkazing."
        )
    except Exception as e:
        messages.error(request, "Kursni o‘chirib bo‘lmadi: " + str(e))

    return redirect(reverse('manage_course'))


def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)

    try:
        subject.delete()
        messages.success(request, "Fan muvaffaqiyatli o‘chirildi.")
    except ProtectedError:
        messages.error(
            request,
            "Bu fan boshqa ma’lumotlar bilan bog‘langan. "
            "Avval bog‘liq ma’lumotlarni o‘chiring."
        )
    except Exception as e:
        messages.error(request, "Fanni o‘chirib bo‘lmadi: " + str(e))

    return redirect(reverse('manage_subject'))


def delete_session(request, session_id):
    session = get_object_or_404(Session, id=session_id)

    try:
        session.delete()
        messages.success(request, "O‘quv yili muvaffaqiyatli o‘chirildi.")
    except Exception:
        messages.error(
            request,
            "Bu o‘quv yiliga biriktirilgan talabalar mavjud. "
            "Iltimos, avval ularni boshqa o‘quv yiliga o‘tkazing."
        )

    return redirect(reverse('manage_session'))
