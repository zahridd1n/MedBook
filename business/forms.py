from django import forms
from .models import Business, WorkingHours, FAQ

# O'zbekiston shaharlari (standart yozuv)
UZBEKISTAN_CITIES = [
    "Toshkent", "Samarqand", "Namangan", "Andijon", "Farg'ona",
    "Buxoro", "Nukus", "Qarshi", "Jizzax", "Guliston",
    "Termiz", "Navoiy", "Urganch", "Margilon", "Chirchiq",
    "Qo'qon", "Angren", "Almaliq", "Bekobod", "Yangiyer",
    "Zarafshon", "Muborak", "G'azalkent", "Salor", "Turon",
    "Kitob", "Shaxrisabz", "Denov", "Shahrisabz", "Xiva",
    "Kattaqo'rg'on", "Kogon", "Qibray", "To'rtko'l", "Xo'jayli",
    "Gurlan", "Hazorasp", "Pitnak", "Sho'rchi", "Boysun",
]

# Normalizatsiya uchun mapping (kichik harf → standart yozuv)
_CITY_LOWER_MAP = {c.lower(): c for c in UZBEKISTAN_CITIES}
# Inglizcha variantlari ham qo'shamiz
_CITY_LOWER_MAP.update({
    'tashkent': 'Toshkent', 'samarkand': 'Samarqand',
    'namangan': 'Namangan', 'andijan': 'Andijon',
    'fergana': "Farg'ona", 'fargona': "Farg'ona",
    'bukhara': 'Buxoro', 'buхoro': 'Buxoro',
    'nukus': 'Nukus', 'karshi': 'Qarshi',
    'jizzax': 'Jizzax', 'guliston': 'Guliston',
    'termez': 'Termiz', 'navoi': 'Navoiy',
    'urgench': 'Urganch', 'margilan': 'Margilon',
    'chirchiq': 'Chirchiq', 'kokand': "Qo'qon",
    'angren': 'Angren', 'almalyk': 'Almaliq',
})

class BusinessSetupForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = (
            'name', 'category', 'about', 'logo',
            'phone', 'email', 'address', 'city',
            'latitude', 'longitude',
            'telegram', 'instagram', 'website',
            'show_in_directory',
        )
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'about': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'list': 'city-datalist',
                'placeholder': "Shahar tanlang...",
                'autocomplete': 'off',
            }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'telegram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'show_in_directory': forms.CheckboxInput(attrs={'class': 'ios-toggle', 'id': 'id_show_in_directory'}),
        }

    def clean_city(self):
        """Normalize city name: strip, title-case, map to standard Uzbek spelling."""
        city = self.cleaned_data.get('city', '').strip()
        if not city:
            return city
        normalized = _CITY_LOWER_MAP.get(city.lower())
        if normalized:
            return normalized
        # Fallback: title-case what they typed
        return city.strip().title()


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ('question', 'answer', 'order', 'is_active')
        widgets = {
            'question': forms.TextInput(attrs={'class': 'form-control'}),
            'answer': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class SEOForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ('meta_title', 'meta_description', 'meta_keywords', 'og_image')
        widgets = {
            'meta_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SEO title (bo\'sh qoldirilsa biznes nomi ishlatiladi)', 'maxlength': 70}),
            'meta_description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Meta description (bo\'sh qoldirilsa "about" ishlatiladi)', 'rows': 3, 'maxlength': 160}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kalit so\'zlar (vergul bilan ajrating)'}),
            'og_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class BrandingForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ('primary_color', 'banner_image', 'button_style', 'card_shadow', 'navbar_style', 'custom_css')
        widgets = {
            'primary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color', 'style': 'height:48px;padding:4px'}),
            'banner_image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'button_style': forms.Select(attrs={'class': 'form-select'}),
            'card_shadow': forms.Select(attrs={'class': 'form-select'}),
            'navbar_style': forms.Select(attrs={'class': 'form-select'}),
            'custom_css': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': '/* Maxsus CSS kodlari (ixtiyoriy) */'}),
        }

    def clean_custom_css(self):
        css = self.cleaned_data.get('custom_css', '')
        if css and self.instance and not self.instance.can_use_custom_css():
            if self.instance.custom_css != css:
                raise forms.ValidationError('Maxsus CSS faqat Max tarifida mavjud.')
        return css
