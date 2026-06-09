from django import forms
from .models import DemandeContact, Reservation, VisiteProgrammee, SiteFoncier, Parcelle, Temoignage
import json

FC = 'width:100%;border:1.5px solid #E5E7EB;border-radius:10px;padding:11px 14px;color:#1F2937;font-family:Outfit,sans-serif;font-size:14px;outline:none;background:#fff;transition:border-color 0.2s;'
SC = 'width:100%;border:1.5px solid #E5E7EB;border-radius:10px;padding:11px 14px;color:#1F2937;font-family:Outfit,sans-serif;font-size:14px;background:#fff;'


class DemandeContactForm(forms.ModelForm):
    class Meta:
        model = DemandeContact
        fields = ['nom', 'email', 'telephone', 'whatsapp', 'type_demande', 'message', 'budget', 'site', 'parcelle']
        widgets = {
            'nom': forms.TextInput(attrs={'style': FC, 'placeholder': 'Votre nom complet'}),
            'email': forms.EmailInput(attrs={'style': FC, 'placeholder': 'votre@email.com'}),
            'telephone': forms.TextInput(attrs={'style': FC, 'placeholder': '+237 6XX XXX XXX'}),
            'whatsapp': forms.TextInput(attrs={'style': FC, 'placeholder': '+237 6XX XXX XXX'}),
            'type_demande': forms.Select(attrs={'style': SC}),
            'message': forms.Textarea(attrs={'style': FC, 'rows': 4, 'placeholder': 'Votre message...'}),
            'budget': forms.TextInput(attrs={'style': FC, 'placeholder': 'Ex: 3 000 000 FCFA'}),
            'site': forms.HiddenInput(),
            'parcelle': forms.HiddenInput(),
        }


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['nom_client', 'email_client', 'telephone_client', 'notes']
        widgets = {
            'nom_client': forms.TextInput(attrs={'style': FC, 'placeholder': 'Nom complet'}),
            'email_client': forms.EmailInput(attrs={'style': FC, 'placeholder': 'Email'}),
            'telephone_client': forms.TextInput(attrs={'style': FC, 'placeholder': '+237 6XX XXX XXX'}),
            'notes': forms.Textarea(attrs={'style': FC, 'rows': 3, 'placeholder': 'Remarques...'}),
        }


class VisiteForm(forms.ModelForm):
    class Meta:
        model = VisiteProgrammee
        fields = ['nom_client', 'telephone_client', 'email_client', 'site', 'date_visite', 'notes']
        widgets = {
            'nom_client': forms.TextInput(attrs={'style': FC, 'placeholder': 'Nom complet'}),
            'telephone_client': forms.TextInput(attrs={'style': FC, 'placeholder': '+237 6XX XXX XXX'}),
            'email_client': forms.EmailInput(attrs={'style': FC, 'placeholder': 'Email'}),
            'site': forms.Select(attrs={'style': SC}),
            'date_visite': forms.DateTimeInput(attrs={'style': FC, 'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'style': FC, 'rows': 2}),
        }


class SiteFoncierForm(forms.ModelForm):
    class Meta:
        model = SiteFoncier
        fields = [
            'nom', 'description', 'description_courte', 'localisation', 'ville', 'quartier',
            'latitude', 'longitude', 'zoom_carte', 'image_principale', 'video_drone',
            'statut', 'prix_min', 'prix_max', 'superficie_totale',
            'featured', 'en_promotion', 'promotion_description', 'promotion_fin',
            'is_active', 'ordre'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            w = field.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs['style'] = 'width:18px;height:18px;cursor:pointer;'
            elif isinstance(w, forms.Select):
                w.attrs['style'] = SC
            elif isinstance(w, forms.Textarea):
                w.attrs['style'] = FC
                w.attrs['rows'] = 3
            elif isinstance(w, forms.DateTimeInput):
                w.attrs['style'] = FC
                w.attrs['type'] = 'datetime-local'
            elif not isinstance(w, forms.FileInput):
                w.attrs['style'] = FC


class ParcelleForm(forms.ModelForm):
    geojson_text = forms.CharField(
        required=False,
        label="GeoJSON (polygone) — dessiné automatiquement via la carte",
        widget=forms.Textarea(attrs={
            'style': FC, 'rows': 3,
            'placeholder': '{"type":"Polygon","coordinates":[[[11.52,3.87],...]]}'
        })
    )

    class Meta:
        model = Parcelle
        fields = [
            'site', 'numero', 'superficie', 'longueur', 'largeur',
            'prix', 'prix_negocie', 'en_promotion', 'prix_promo', 'promo_fin',
            'statut', 'latitude', 'longitude', 'description', 'caracteristiques',
            'featured', 'is_active', 'ordre'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.geojson:
            self.fields['geojson_text'].initial = json.dumps(self.instance.geojson, indent=2)
        for name, field in self.fields.items():
            w = field.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs['style'] = 'width:18px;height:18px;cursor:pointer;'
            elif isinstance(w, forms.Select):
                w.attrs['style'] = SC
            elif isinstance(w, forms.Textarea):
                w.attrs['style'] = FC
                w.attrs['rows'] = 3
            elif isinstance(w, forms.DateTimeInput):
                w.attrs['style'] = FC
                w.attrs['type'] = 'datetime-local'
            elif not isinstance(w, forms.FileInput):
                w.attrs['style'] = FC

    def save(self, commit=True):
        instance = super().save(commit=False)
        geojson_text = self.cleaned_data.get('geojson_text', '').strip()
        if geojson_text:
            try:
                instance.geojson = json.loads(geojson_text)
            except Exception:
                pass
        if commit:
            instance.save()
        return instance


class TemoignageForm(forms.ModelForm):
    class Meta:
        model = Temoignage
        fields = ['nom', 'role', 'avatar', 'texte', 'note', 'site', 'is_active', 'ordre']
        widgets = {
            'nom': forms.TextInput(attrs={'style': FC, 'placeholder': 'Nom du client'}),
            'role': forms.TextInput(attrs={'style': FC, 'placeholder': 'Ex: Entrepreneur, Douala'}),
            'texte': forms.Textarea(attrs={'style': FC, 'rows': 4, 'placeholder': 'Le temoignage...'}),
            'note': forms.Select(attrs={'style': SC}),
            'site': forms.Select(attrs={'style': SC}),
            'ordre': forms.NumberInput(attrs={'style': FC}),
            'is_active': forms.CheckboxInput(attrs={'style': 'width:18px;height:18px;'}),
        }