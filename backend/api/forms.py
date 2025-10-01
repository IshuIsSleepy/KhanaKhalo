# api/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import University, Profile

class UserRegisterForm(UserCreationForm):
    # We define all the fields here, including ones for the Profile model
    email = forms.EmailField(required=True)
    roll_no = forms.CharField(max_length=50, required=True, label="Roll Number")
    university = forms.ModelChoiceField(
        queryset=University.objects.all(),
        required=True,
        empty_label="Select your university"
    )
    phone = forms.CharField(max_length=15, required=False, label="Phone (Optional)")

    class Meta(UserCreationForm.Meta):
        model = User
        # IMPORTANT: The 'fields' in Meta should only contain fields for the User model.
        # The extra fields (roll_no, etc.) are handled by the form itself.
        fields = UserCreationForm.Meta.fields + ('email',)

    def clean(self):
        """
        Custom validation to check if the email domain matches the selected university.
        """
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        university = cleaned_data.get('university')

        if email and university:
            email_domain = email.split('@')[-1]
            if university.domain and email_domain != university.domain:
                raise forms.ValidationError(
                    "Your email domain must match the selected university's domain "
                    f"(@{university.domain})."
                )
        
        # Check if email already exists
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
            
        return cleaned_data

    def save(self, commit=True):
        # First, save the User object
        user = super().save(commit=False)
        # The UserCreationForm doesn't save the email by default, so we do it here
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Now, create the associated Profile object with the extra data
            Profile.objects.create(
                user=user,
                university=self.cleaned_data['university'],
                roll_no=self.cleaned_data['roll_no'],
                phone=self.cleaned_data.get('phone', '') # Use .get for optional fields
            )
        return user