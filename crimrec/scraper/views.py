from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import CriminalRecord

def record_list(request):
    query = request.GET.get('q', '')
    parish_filter = request.GET.get('parish', '')
    
    records = CriminalRecord.objects.all().order_by('-date_filed')
    
    if query:
        records = records.filter(
            Q(defendant_name__icontains=query) |
            Q(case_number__icontains=query) |
            Q(charges__icontains=query)
        )
    
    if parish_filter:
        records = records.filter(parish__iexact=parish_filter)
    
    paginator = Paginator(records, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    parishes = CriminalRecord.objects.values_list('parish', flat=True).distinct().order_by('parish')
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'parishes': parishes,
        'selected_parish': parish_filter,
        'total_records': records.count(),
    }
    return render(request, 'scraper/record_list.html', context)

def record_detail(request, pk):
    record = get_object_or_404(CriminalRecord, pk=pk)
    charges_list = record.charges.split('\n') if record.charges else []
    context = {
        'record': record,
        'charges_list': charges_list,
    }
    return render(request, 'scraper/record_detail.html', context)

