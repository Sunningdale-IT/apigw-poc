"""
Forms for Certosaur certificate management. 🦖
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import CertificateAuthority, ServerCertificate, ClientCertificate


class StyledFormMixin:
    """Mixin to add consistent styling to form fields."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            css_class = 'form-input'
            if isinstance(field.widget, forms.Select):
                css_class = 'form-select'
            elif isinstance(field.widget, forms.Textarea):
                css_class = 'form-textarea'
            elif isinstance(field.widget, forms.CheckboxInput):
                css_class = 'form-checkbox'
            
            field.widget.attrs.update({
                'class': css_class,
            })


class LoginForm(StyledFormMixin, AuthenticationForm):
    """Custom login form with styling."""
    pass


class CertificateAuthorityForm(StyledFormMixin, forms.ModelForm):
    """Form for creating Certificate Authorities."""
    
    validity_days = forms.IntegerField(
        initial=3650,
        min_value=1,
        max_value=7300,
        help_text='Number of days the CA certificate will be valid (default: 10 years)'
    )
    key_size = forms.ChoiceField(
        choices=[(2048, '2048-bit'), (4096, '4096-bit')],
        initial=4096,
        help_text='RSA key size (4096-bit recommended for CAs)'
    )
    
    class Meta:
        model = CertificateAuthority
        fields = [
            'name', 'common_name', 'organization', 'organizational_unit',
            'country', 'state', 'locality', 'parent_ca'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'My Root CA'}),
            'common_name': forms.TextInput(attrs={'placeholder': 'My Organization Root CA'}),
            'organization': forms.TextInput(attrs={'placeholder': 'My Organization'}),
            'organizational_unit': forms.TextInput(attrs={'placeholder': 'IT Security'}),
            'country': forms.TextInput(attrs={'placeholder': 'US', 'maxlength': 2}),
            'state': forms.TextInput(attrs={'placeholder': 'California'}),
            'locality': forms.TextInput(attrs={'placeholder': 'San Francisco'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent_ca'].queryset = CertificateAuthority.objects.all()
        self.fields['parent_ca'].required = False
        self.fields['parent_ca'].empty_label = '-- Create as Root CA --'


class CAChoiceField(forms.ModelChoiceField):
    """Custom choice field that shows Root/Intermediate labels."""
    
    def label_from_instance(self, obj):
        if obj.is_root:
            return f"🦖 {obj.name} (ROOT CA)"
        else:
            return f"🦕 {obj.name} (Intermediate)"


class ServerCertificateForm(StyledFormMixin, forms.ModelForm):
    """Form for creating Server Certificates."""
    
    issuing_ca = CAChoiceField(
        queryset=CertificateAuthority.objects.all(),
        help_text='Select which CA will sign this certificate. Intermediate CAs are recommended.'
    )
    
    validity_days = forms.IntegerField(
        initial=365,
        min_value=1,
        max_value=825,  # Max 2 years per CA/Browser Forum guidelines
        help_text='Number of days the certificate will be valid (max: 825 days)'
    )
    
    class Meta:
        model = ServerCertificate
        fields = [
            'name', 'common_name', 'san_dns_names', 'san_ip_addresses',
            'organization', 'organizational_unit', 'country', 'state', 'locality',
            'issuing_ca', 'key_size'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Production Web Server'}),
            'common_name': forms.TextInput(attrs={'placeholder': 'www.example.com'}),
            'san_dns_names': forms.Textarea(attrs={
                'placeholder': 'example.com, api.example.com, *.example.com',
                'rows': 3
            }),
            'san_ip_addresses': forms.Textarea(attrs={
                'placeholder': '192.168.1.1, 10.0.0.1',
                'rows': 2
            }),
            'organization': forms.TextInput(attrs={'placeholder': 'My Organization'}),
            'organizational_unit': forms.TextInput(attrs={'placeholder': 'IT Operations'}),
            'country': forms.TextInput(attrs={'placeholder': 'US', 'maxlength': 2}),
            'state': forms.TextInput(attrs={'placeholder': 'California'}),
            'locality': forms.TextInput(attrs={'placeholder': 'San Francisco'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order by is_root (False first = Intermediates first)
        self.fields['issuing_ca'].queryset = CertificateAuthority.objects.order_by('is_root', 'name')


class ClientCertificateForm(StyledFormMixin, forms.ModelForm):
    """Form for creating Client Certificates."""
    
    issuing_ca = CAChoiceField(
        queryset=CertificateAuthority.objects.all(),
        help_text='Select which CA will sign this certificate. Intermediate CAs are recommended.'
    )
    
    validity_days = forms.IntegerField(
        initial=365,
        min_value=1,
        max_value=1095,  # Max 3 years
        help_text='Number of days the certificate will be valid (max: 3 years)'
    )
    generate_p12 = forms.BooleanField(
        initial=True,
        required=False,
        help_text='Generate a PKCS#12 bundle for easy import into browsers'
    )
    
    class Meta:
        model = ClientCertificate
        fields = [
            'name', 'common_name', 'email',
            'organization', 'organizational_unit', 'country', 'state', 'locality',
            'issuing_ca', 'key_size'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'John Doe Client Cert'}),
            'common_name': forms.TextInput(attrs={'placeholder': 'john.doe@example.com'}),
            'email': forms.EmailInput(attrs={'placeholder': 'john.doe@example.com'}),
            'organization': forms.TextInput(attrs={'placeholder': 'My Organization'}),
            'organizational_unit': forms.TextInput(attrs={'placeholder': 'Engineering'}),
            'country': forms.TextInput(attrs={'placeholder': 'US', 'maxlength': 2}),
            'state': forms.TextInput(attrs={'placeholder': 'California'}),
            'locality': forms.TextInput(attrs={'placeholder': 'San Francisco'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order by is_root (False first = Intermediates first)
        self.fields['issuing_ca'].queryset = CertificateAuthority.objects.order_by('is_root', 'name')


class RevokeCertificateForm(StyledFormMixin, forms.Form):
    """Form for revoking certificates."""
    
    REASON_CHOICES = [
        ('unspecified', 'Unspecified'),
        ('key_compromise', 'Key Compromise'),
        ('ca_compromise', 'CA Compromise'),
        ('affiliation_changed', 'Affiliation Changed'),
        ('superseded', 'Superseded'),
        ('cessation_of_operation', 'Cessation of Operation'),
    ]
    
    reason = forms.ChoiceField(choices=REASON_CHOICES)
    confirm = forms.BooleanField(
        required=True,
        help_text='I confirm that I want to revoke this certificate'
    )
