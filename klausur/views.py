import datetime
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from .models import Klausur, Klausurthema, Frage, Teilnehmer, Answer
from django.db.models import Sum, Avg
import locale, random
from django.contrib.auth.decorators import permission_required

from . import renderers

locale.setlocale(locale.LC_ALL, "")
# Create your views here.

def start(request):
    return render(request, "start.html")

def pdf_view(self, request, *args, **kwargs):
    data = {
        'today': datetime.date.today(),
        'amount': 39.99,
        'customer_name': 'Cooper Mann',
        'invoice_number': 1233434,
    }
    return renderers.render_to_pdf('pdfs/invoice.html', data)


def advanced_pdf_view(request):
    thema = "Testklausur"
    fragen = Frage.objects.all()
    context = {
        'thema': thema,
        'fragen': fragen,
    }
    response = renderers.render_to_pdf("pdfs/klausur.html", context)
    if response.status_code == 404:
        raise Http404("Invoice not found")

    filename = f"Klausur_{thema}.pdf"
    """
    Tell browser to view inline (default)
    """
    content = f"inline; filename={filename}"
    download = request.GET.get("download")
    if download:
        """
        Tells browser to initiate download
        """
        content = f"attachment; filename={filename}"
    response["Content-Disposition"] = content
    return response

@permission_required('klausur.view_teilnehmer')
def gen_pdf(request, id, typ):
    # fragen = Klausurthema.objects.filter(klausur=id)
    # typ 1 - Klausur, 
    #     2 - Muster
    #     3 - Design Fragen
    #     4 - Design Muster
    klausur = Klausur.objects.get(pk=id)
    fragen = []
    if typ == 1 or typ == 2:
        pfragen = klausur.fragen.all()
        for pfrage in pfragen:
            fragen.append((pfrage, False))
    elif typ == 3 or typ == 4:
        pfragen = Klausurthema.objects.filter(klausur=klausur)
        for pfrage in pfragen:
            fragen.append((pfrage.frage,pfrage.seitenwechsel))
    thema = klausur.titel
    punkte = klausur.get_gesamtpunkte
    termin = klausur.termin.date()
    context = {
        'klausur': klausur,
        'fragen': fragen,
        'termin': termin,
        'punkte': punkte,
        'thema': thema,
    }
    if typ == 1 or typ == 3: # Klausur
        response = renderers.render_to_pdf("pdfs/klausur_gen.html", context)
    elif typ == 2 or typ == 4: # Muster
        response = renderers.render_to_pdf("pdfs/muster_gen.html", context)        
    
    if response.status_code == 404:
        raise Http404("Invoice not found")

    filename = f"Klausur_{thema}.pdf"
    """
    Tell browser to view inline (default)
    """
    content = f"inline; filename={filename}"
    download = request.GET.get("download")
    if download:
        """
        Tells browser to initiate download
        """
        content = f"attachment; filename={filename}"
    response["Content-Disposition"] = content
    return response

@permission_required('klausur.view_teilnehmer')
def klaus_design(request, id):
    ds_klausur = Klausur.objects.get(pk=id)
    fragen = ds_klausur.fragen.all()
    i = 0
    # Fragen eintragen
    for frage in fragen:
        position, created = Klausurthema.objects.get_or_create(klausur = ds_klausur, frage=frage)
        if created:
            position.position = i
            position.save()        
        i +=1

    # Datenbank leeren
    fragen = Klausurthema.objects.filter(klausur=ds_klausur)
    # print(fragen)
    for frage in fragen:
        if not ds_klausur.fragen.filter(id=frage.frage.id).exists():
            Klausurthema.objects.get(frage=frage.frage, klausur=ds_klausur).delete()
    pos_fragen = Klausurthema.objects.filter(klausur = ds_klausur)
    lst_fragen = []
    for frage in pos_fragen:
        sum=Answer.objects.filter(klausur = ds_klausur, frage=frage.frage).aggregate(Avg("punkte"))['punkte__avg']
        if sum is not None:
            sum=str(round(Answer.objects.filter(klausur = ds_klausur, frage=frage.frage).aggregate(Avg("punkte"))['punkte__avg']/frage.frage.punkte*100,1))+"%"
        else:
            sum=""
        lst_fragen.append((frage, sum))
    content = {
        'klausur': ds_klausur,
        'fragen': lst_fragen,
    }
    return render(request, "design.html", content)

@permission_required('klausur.view_teilnehmer')
def richtung(request, klausur, frage, richtung):
    klausur = Klausur.objects.get(pk=klausur)
    frage = Frage.objects.get(pk=frage)
    position = Klausurthema.objects.get(klausur=klausur, frage=frage)
    if richtung==1 :
        position.position += 2
    elif richtung==2:
        position.position -= 2
    position.save()
    return redirect("/klausur/design/"+str(klausur.pk))

@permission_required('klausur.view_teilnehmer')
def zufall(request, klausur):
    lst = list(range(len(Klausurthema.objects.filter(klausur = Klausur.objects.get(pk=klausur)))))
    fragen = Klausurthema.objects.filter(klausur=Klausur.objects.get(pk=klausur))
    for frage in fragen:
        pos = random.choice(lst)
        lst.remove(pos)
        frage.position=pos
        frage.seitenwechsel = False
        frage.save()
    return redirect("/klausur/design/"+str(klausur))

@permission_required('klausur.view_teilnehmer')
def newside(request, klausur):    
    frage=request.POST['nl']
    if frage == "gen":
        gen_pdf(request, klausur, 3)
    else:    
        ds = Klausurthema.objects.get(id=frage)
        ds.seitenwechsel = not ds.seitenwechsel
        ds.save()
        print(ds.frage)
    return redirect("/klausur/design/"+str(klausur))

@permission_required('klausur.view_teilnehmer')
def evaluation(request, klausur):
    ds_klausur = Klausur.objects.get(id=klausur)
    ds_tn = ds_klausur.gruppe.teilnehmer.all()
    lst_tn = []
    for tn in ds_tn:
        punkte = Answer.objects.filter(teilnehmer = tn, klausur = ds_klausur).aggregate(Sum("punkte"))['punkte__sum']
        if punkte != None:
            prozent = round(punkte / ds_klausur.get_gesamtpunkte * 100, 1)
        else:
            prozent = 0
        lst_tn.append((tn, punkte, prozent))
    content = {
        "klausur": ds_klausur,
        "teilnehmer": lst_tn,
    }
    return render(request, "evaluation.html", content)

@permission_required('klausur.view_teilnehmer')
def evaluation2(request, klausur, tn):
    # Daten aus DB lesen
    ds_klausur = Klausur.objects.get(id=klausur)
    ds_tn = Teilnehmer.objects.get(id=tn)
    ds_fragen = ds_klausur.fragen.all()
    pos_fragen = Klausurthema.objects.filter(klausur = klausur)
    list_fragen = []
    # Gesamtsumme Punkte berechnen
    sum = 0    
    for frage in pos_fragen:    
        if request.method == "POST":
            # Aus Formular einlesen
            numb_str = request.POST["punkte_"+str(frage.frage.id)]
            # Eingabefeld ausgefüllt?
            if len(numb_str) > 0:
                number = int(numb_str)
            else:
                number = 0
        else:
            # Aus DS einlesen
            ds_answer=Answer.objects.filter(teilnehmer=ds_tn, klausur=ds_klausur, frage=frage.frage)
            if len(ds_answer) == 0:                                     # Kein DS vorhanden
                number=0
            else:
                number=ds_answer[0].punkte
        sum += number
        # Liste Fragen + Punkte erweitern
        list_fragen.append((frage, number))
        prozent = round(sum / ds_klausur.get_gesamtpunkte * 100, 1)
    if "button" in request.POST:
        if request.POST["button"] == "save":
            # Datensätze speichern
            for frage in list_fragen:
                ds_frage = Frage.objects.get(id=frage[0].frage.id)
                answer, created = Answer.objects.get_or_create(teilnehmer=ds_tn, klausur=ds_klausur, frage=ds_frage)
                answer.punkte = frage[1]
                answer.save()
            return redirect('evaluation', klausur=str(ds_klausur.id))

    content = {
        "klausur": ds_klausur,
        "teilnehmer": ds_tn,
        "fragen": list_fragen,
        "sum": sum,
        "max": ds_klausur.get_gesamtpunkte,
        "prozent": prozent
    }
    return render(request, "evaluation2.html", content)
