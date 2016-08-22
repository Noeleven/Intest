from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def tyindex(request):
	return render(request, 'TYreport_2016-08-16.html')
def tyreport(request):
	return render(request, 'TYreport.html')
