from .models import VideoGlobale

def video_globale_context(request):
    """Ajoute la vidéo globale à toutes les pages"""
    try:
        video = VideoGlobale.objects.filter(is_active=True).first()
        return {'video_globale': video}
    except Exception:
        return {'video_globale': None}