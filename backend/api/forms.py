
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import University, Profile

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    roll_no = forms.CharField(max_length=50, required=True, label="Roll Number")
    university = forms.ModelChoiceField(
        queryset=University.objects.all(),
        required=False,
        empty_label="Select your university"
    )
    phone = forms.CharField(max_length=15, required=False, label="Phone (Optional)")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        university = cleaned_data.get('university')

        if email:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("This email address is already registered.")


            email_domain = email.split('@')[-1]
            try:
                matched_university = University.objects.get(domain=email_domain)

                cleaned_data['university'] = matched_university
            except University.DoesNotExist:

                if not university:
                    self.add_error('university', 'Your email domain does not match a registered university. Please select one manually.')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                university=self.cleaned_data['university'],
                roll_no=self.cleaned_data['roll_no'],
                phone=self.cleaned_data.get('phone', '')
            )
        return user