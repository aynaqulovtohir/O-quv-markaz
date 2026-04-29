from django import forms
from django.forms.widgets import DateInput, TextInput

from .models import *


class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'


class CustomUserForm(FormSettings):
    email = forms.EmailField(required=True)
    gender = forms.ChoiceField(choices=[('E', 'Erkak'), ('A', 'Ayol')])
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea)
    password = forms.CharField(widget=forms.PasswordInput)
    widget = {
        'password': forms.PasswordInput(),
    }
    profile_pic = forms.ImageField()

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)

        if kwargs.get('instance'):
            instance = kwargs.get('instance').admin.__dict__
            self.fields['password'].required = False
            for field in CustomUserForm.Meta.fields:
                self.fields[field].initial = instance.get(field)
            if self.instance.pk is not None:
                self.fields['password'].widget.attrs['placeholder'] = "Agar parolni yangilamoqchi bo‘lsangizgina, ushbu maydonni to‘ldiring."

    def clean_email(self):
        formEmail = self.cleaned_data['email'].lower()

        if self.instance.pk is None:  # Yangi foydalanuvchi
            if CustomUser.objects.filter(email=formEmail).exists():
                raise forms.ValidationError(
                    "Kiritilgan elektron pochta manzili allaqachon ro‘yxatdan o‘tgan."
                )
        else:  # Tahrirlash
            dbEmail = self.Meta.model.objects.get(
                id=self.instance.pk
            ).admin.email.lower()

            if dbEmail != formEmail:
                if CustomUser.objects.filter(email=formEmail).exists():
                    raise forms.ValidationError(
                        "Kiritilgan elektron pochta manzili allaqachon ro‘yxatdan o‘tgan."
                    )

        return formEmail

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'gender',  'password','profile_pic', 'address' ]


class StudentForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = CustomUserForm.Meta.fields + \
            ['course', 'session']


class AdminForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(AdminForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Admin
        fields = CustomUserForm.Meta.fields


class StaffForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StaffForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Staff
        fields = CustomUserForm.Meta.fields + \
            ['course' ]


class CourseForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)

    class Meta:
        fields = ['name']
        model = Course


class SubjectForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(SubjectForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Subject
        fields = ['name', 'staff', 'course']


class SessionForm(FormSettings):

    class Meta:
        model = Session
        fields = '__all__'

        labels = {
            'start_year': "Boshlanish sanasi",
            'end_year': "Tugash sanasi",
        }

        widgets = {
            'start_year': DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'end_year': DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }

    # ✅ Sana tekshiruvi
    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_year')
        end = cleaned_data.get('end_year')

        if start and end:
            if start >= end:
                raise forms.ValidationError(
                    "Tugash sanasi boshlanish sanasidan katta bo‘lishi kerak."
                )

        return cleaned_data


class LeaveReportStaffForm(FormSettings):

    class Meta:
        model = LeaveReportStaff
        fields = ['date', 'message']

        labels = {
            'date': "Ta’til sanasi",
            'message': "Ta’til sababi"
        }

        widgets = {
            'date': DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': "Ta’til sababini kiriting..."
            })
        }

    # ✅ Sana tekshiruvi (bugundan oldingi sana bo‘lmasin)
    def clean_date(self):
        date = self.cleaned_data.get('date')

        if date:
            from datetime import date as today_date
            if date < today_date.today():
                raise forms.ValidationError(
                    "Ta’til sanasi bugungi kundan oldin bo‘lishi mumkin emas."
                )

        return date


class FeedbackStaffForm(FormSettings):

    class Meta:
        model = FeedbackStaff
        fields = ['feedback']

        labels = {
            'feedback': "Fikr-mulohaza"
        }

        widgets = {
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': "Fikr yoki taklifingizni yozing..."
            })
        }

    # ✅ Bo‘sh yuborilmasin
    def clean_feedback(self):
        feedback = self.cleaned_data.get('feedback')

        if not feedback or len(feedback.strip()) < 5:
            raise forms.ValidationError(
                "Fikr kamida 5 ta belgidan iborat bo‘lishi kerak."
            )

        return feedback


class LeaveReportStudentForm(FormSettings):

    class Meta:
        model = LeaveReportStudent
        fields = ['date', 'message']

        labels = {
            'date': "Ta’til sanasi",
            'message': "Ta’til sababi"
        }

        widgets = {
            'date': DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': "Ta’til sababini kiriting..."
            })
        }

    # ✅ Sana tekshiruvi
    def clean_date(self):
        date = self.cleaned_data.get('date')

        if date:
            from datetime import date as today_date
            if date < today_date.today():
                raise forms.ValidationError(
                    "Ta’til sanasi bugungi kundan oldin bo‘lishi mumkin emas."
                )

        return date


class FeedbackStudentForm(FormSettings):

    class Meta:
        model = FeedbackStudent
        fields = ['feedback']

        labels = {
            'feedback': "Fikr-mulohaza"
        }

        widgets = {
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': "Fikr yoki taklifingizni yozing..."
            })
        }

    # ✅ Minimal uzunlik tekshiruvi
    def clean_feedback(self):
        feedback = self.cleaned_data.get('feedback')

        if not feedback or len(feedback.strip()) < 5:
            raise forms.ValidationError(
                "Fikr kamida 5 ta belgidan iborat bo‘lishi kerak."
            )

        return feedback


class StudentEditForm(CustomUserForm):

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = CustomUserForm.Meta.fields + ['course', 'session']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].required = False
        self.fields['password'].widget.attrs['placeholder'] = (
            "Parolni o‘zgartirmoqchi bo‘lsangizgina kiriting"
        )


class StaffEditForm(CustomUserForm):

    class Meta(CustomUserForm.Meta):
        model = Staff
        fields = CustomUserForm.Meta.fields + ['course']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].required = False
        self.fields['password'].widget.attrs['placeholder'] = (
            "Parolni o‘zgartirmoqchi bo‘lsangizgina kiriting"
        )


class EditResultForm(FormSettings):

    session_year = forms.ModelChoiceField(
        label="O‘quv yili",
        queryset=Session.objects.none(),
        required=True
    )

    class Meta:
        model = StudentResult
        fields = ['session_year', 'subject', 'student', 'test', 'exam']

        labels = {
            'subject': "Fan",
            'student': "Talaba",
            'test': "Test bali",
            'exam': "Imtihon bali",
        }

        widgets = {
            'test': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100
            }),
            'exam': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Har safar yangilanadi
        self.fields['session_year'].queryset = Session.objects.all()

    # ✅ Ball validatsiyasi
    def clean(self):
        cleaned_data = super().clean()
        test = cleaned_data.get('test')
        exam = cleaned_data.get('exam')

        if test is not None and exam is not None:
            if test > 100 or exam > 100:
                raise forms.ValidationError(
                    "Ball 100 dan oshmasligi kerak."
                )

        return cleaned_data
