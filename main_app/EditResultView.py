from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib import messages
from .models import Subject, Staff, Student, StudentResult
from .forms import EditResultForm
from django.urls import reverse

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

class EditResultView(View):
    def get(self, request, *args, **kwargs):
        resultForm = EditResultForm()
        staff = get_object_or_404(Staff, admin=request.user)

        # O‘qituvchiga biriktirilgan fanlar chiqsin
        resultForm.fields['subject'].queryset = Subject.objects.filter(staff=staff)

        context = {
            'form': resultForm,
            'page_title': "Natijani tahrirlash"
        }
        return render(request, "staff_template/edit_student_result.html", context)

    def post(self, request, *args, **kwargs):
        form = EditResultForm(request.POST)
        staff = get_object_or_404(Staff, admin=request.user)

        form.fields['subject'].queryset = Subject.objects.filter(staff=staff)

        context = {'form': form, 'page_title': "Natijani tahrirlash"}

        if form.is_valid():
            student = form.cleaned_data.get('student')
            subject = form.cleaned_data.get('subject')
            test = form.cleaned_data.get('test')
            exam = form.cleaned_data.get('exam')

            try:

                result, created = StudentResult.objects.update_or_create(
                    student=student,
                    subject=subject,
                    defaults={'test': test, 'exam': exam}
                )

                if created:
                    messages.success(request, "Natija yaratildi va muvaffaqiyatli saqlandi.")
                else:
                    messages.success(request, "Natija muvaffaqiyatli yangilandi.")

                return redirect(reverse('edit_student_result'))

            except Exception as e:
                messages.warning(request, "Natijani saqlashda xatolik yuz berdi: " + str(e))
        else:
            messages.warning(request, "Forma noto‘g‘ri to‘ldirilgan. Iltimos, qayta tekshiring.")

        return render(request, "staff_template/edit_student_result.html", context)