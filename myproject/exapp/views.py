from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login
from .models import Totalsolutions
import pandas as pd
from django.contrib import messages
from django.db import IntegrityError
from django.urls import reverse
import json
from django.views.decorators.csrf import csrf_exempt
import secrets
from django.core.exceptions import ValidationError
from datetime import datetime
import os


@login_required
def home(request):
    total_items = Totalsolutions.objects.count()
    category_software = Totalsolutions.objects.filter(category="software").count()
    category_hardware = Totalsolutions.objects.filter(category="hardware").count()
    category_services = Totalsolutions.objects.filter(category="service").count()

    context = {
        "total_items": total_items,
        "category_software": category_software,
        "category_hardware": category_hardware,
        "category_services": category_services,
    }
    return render(request, "home.html", context)


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('exapp:home')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')


def totalsolutions(request):
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', 'all')
    
    products = Totalsolutions.objects.all()
    
    if search_query:
        products = products.filter(product_name__icontains=search_query)
    
    if category_filter != 'all':
        products = products.filter(category=category_filter)
    
    category_options = ['all', 'software', 'hardware', 'service']
    
    return render(request, 'totalsolutions.html', {
        'objs': products,
        'category_filter': category_filter,
        'search_query': search_query,
        'category_options': category_options,
        'csrf_token': request.COOKIES.get('csrftoken', '')
    })


@login_required
def search_products(request):
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', 'all')
    
    products = Totalsolutions.objects.all()
    
    if search_query:
        products = products.filter(product_name__icontains=search_query)
    
    if category_filter != 'all':
        products = products.filter(category=category_filter)
    
    data = [
        {
            'id': obj.id,
            'application': obj.application or 'NAN',
            'category': obj.category or 'NAN',
            'product_name': obj.product_name or 'NAN',
            'product_image': obj.product_image.url if obj.product_image else None,
            'make': obj.make or 'NAN',
            'model': obj.model or 'NAN',
            'specification': obj.specification or 'NAN',
            'uom': obj.uom or 'NAN',
            'buying_price': float(obj.buying_price) if obj.buying_price is not None else 'NAN',
            'buying_price_color': obj.buying_price_color,
            'vendor': obj.vendor or 'NAN',
            'quotation_received_month': obj.quotation_received_month or 'NAN',
            'lead_time': obj.lead_time or 'NAN',
            'remarks': obj.remarks or 'NAN',
            'list_price': float(obj.list_price) if obj.list_price is not None else 'NAN',
            'discount': int(obj.discount) if obj.discount is not None else 'NAN',
            'sales_price': float(obj.sales_price) if obj.sales_price is not None else 'NAN',
            'sales_margin': int(obj.sales_margin) if obj.sales_margin is not None else 'NAN',
        } for obj in products
    ]
    
    return JsonResponse({'products': data})


@login_required
def additem(request):
    if request.method == 'POST':
        try:
            buying_price = float(request.POST.get('buying_price', 0))
            list_price = float(request.POST.get('list_price', 0))
            discount = int(float(request.POST.get('discount', 0)))

            item = Totalsolutions(
                application=request.POST.get('application') or None,
                category=request.POST.get('category') or None,
                product_name=request.POST.get('product_name') or None,
                make=request.POST.get('make') or None,
                model=request.POST.get('model') or None,
                specification=request.POST.get('specification') or None,
                uom=request.POST.get('uom') or None,
                buying_price=buying_price,
                vendor=request.POST.get('vendor') or None,
                quotation_received_month=request.POST.get('quotation_received_month') or None,
                lead_time=request.POST.get('lead_time') or None,
                remarks=request.POST.get('remarks') or None,
                list_price=list_price,
                discount=discount,
            )
            if 'product_image' in request.FILES:
                item.product_image = request.FILES['product_image']
            item.save()
            messages.success(request, "Item added successfully.")
        except (ValueError, IntegrityError) as e:
            messages.error(request, f"Error adding item: {str(e)}")
        return redirect('exapp:totalsolutions')
    return render(request, 'totalsolutions.html')


@login_required
def delete_all(request):
    if request.method == 'POST':
        for item in Totalsolutions.objects.all():
            if item.product_image and os.path.isfile(item.product_image.path):
                os.remove(item.product_image.path)
        Totalsolutions.objects.all().delete()
        messages.success(request, 'All items have been deleted successfully.')
    return redirect('exapp:totalsolutions')


@login_required
def delete(request, id):
    item = get_object_or_404(Totalsolutions, id=id)
    if request.method == 'POST':
        item_name = str(item)
        if item.product_image and os.path.isfile(item.product_image.path):
            os.remove(item.product_image.path)
        item.delete()
        messages.success(request, f'The item "{item_name}" has been successfully deleted.')
        return redirect('exapp:totalsolutions')
    return render(request, 'totalsolutions.html', {'item': item})


@login_required
def edit(request, id):
    item = get_object_or_404(Totalsolutions, id=id)

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            field = data.get('field')
            value = data.get('value')

            if field in [
                'application', 'category', 'product_name', 'make', 'model',
                'specification', 'uom', 'buying_price', 'vendor',
                'quotation_received_month', 'lead_time', 'remarks',
                'list_price', 'discount', 'sales_price', 'sales_margin'
            ]:
                if field == 'list_price':
                    value = max(float(value), 0)
                    item.list_price = value
                    item.save()
                elif field == 'discount':
                    value = int(float(value.replace('%', '')))
                    item.discount = value
                    item.save()
                elif field == 'buying_price':
                    value = max(float(value), 0)
                    item.buying_price = value
                    item.save()
                else:
                    setattr(item, field, value)
                    item.save(update_fields=[field])

                return JsonResponse({
                    'success': True,
                    'message': f'{field} updated successfully.',
                    'sales_price': item.sales_price,
                    'sales_margin': item.sales_margin,
                    'buying_price': item.buying_price,
                    'buying_price_color': item.buying_price_color
                })
            else:
                return JsonResponse({'success': False, 'message': 'Invalid field.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    if request.method == 'POST':
        try:
            item.application = request.POST.get('application') or None
            item.category = request.POST.get('category') or None
            item.product_name = request.POST.get('product_name') or None
            item.make = request.POST.get('make') or None
            item.model = request.POST.get('model') or None
            item.specification = request.POST.get('specification') or None
            item.uom = request.POST.get('uom') or None
            item.buying_price = max(float(request.POST.get('buying_price', 0)), 0)
            item.vendor = request.POST.get('vendor') or None
            item.quotation_received_month = request.POST.get('quotation_received_month') or None
            item.lead_time = request.POST.get('lead_time') or None
            item.remarks = request.POST.get('remarks') or None
            item.list_price = max(float(request.POST.get('list_price', 0)), 0)
            item.discount = int(float(request.POST.get('discount', 0)))
            item.save()

            item_name = str(item)
            messages.success(request, f'The item "{item_name}" has been successfully updated.')
            return redirect('exapp:totalsolutions')
        except Exception as e:
            messages.error(request, f'Error updating item: {str(e)}')
            return redirect('exapp:totalsolutions')

    return render(request, 'totalsolutions.html', {'item': item})


@login_required
def upload_file(request):
    category_filter = request.GET.get('category', 'all')
    search_query = request.GET.get('search', '')

    if request.method == 'POST':
        file = request.FILES.get('file')
        category_filter = request.POST.get('category', 'all')
        if file:
            try:
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file, dtype={'quotation_received_month': str})
                elif file.name.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(file, dtype={'quotation_received_month': str})
                else:
                    raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")
                
                df['category'] = df['category'].str.strip().str.lower()
                df = df.dropna(how='all')
                df.columns = df.columns.str.strip().str.lower()

                required_columns = [
                    'application', 'category', 'product_name', 'make', 'model', 'specification',
                    'uom', 'buying_price', 'vendor', 'quotation_received_month',
                    'lead_time', 'remarks', 'list_price', 'discount'
                ]
                missing_columns = set(required_columns) - set(df.columns)
                if missing_columns:
                    raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
                
                if category_filter != 'all' and category_filter in ['software', 'hardware', 'service']:
                    df = df[df['category'] == category_filter.lower()]
                
                skipped_duplicates = []
                saved_entries = 0

                for _, row in df.iterrows():
                    try:
                        exists = Totalsolutions.objects.filter(
                            application=row['application'],
                            category=row['category'],
                            product_name=row['product_name'],
                            make=row['make'],
                            model=row['model'],
                        ).exists()

                        if not exists:
                            row_dict = row.to_dict()
                            buying_price = float(row_dict.get('buying_price', 0))
                            list_price = float(row_dict.get('list_price', 0))
                            discount = int(float(row_dict.get('discount', 0)))

                            item = Totalsolutions(
                                application=row_dict.get('application'),
                                category=row_dict.get('category'),
                                product_name=row_dict.get('product_name'),
                                make=row_dict.get('make'),
                                model=row_dict.get('model'),
                                specification=row_dict.get('specification'),
                                uom=row_dict.get('uom'),
                                buying_price=buying_price,
                                vendor=row_dict.get('vendor'),
                                quotation_received_month=row_dict.get('quotation_received_month'),
                                lead_time=row_dict.get('lead_time'),
                                remarks=row_dict.get('remarks'),
                                list_price=list_price,
                                discount=discount,
                            )
                            item.save()
                            saved_entries += 1
                        else:
                            skipped_duplicates.append(row.to_dict())
                    except (ValueError, IntegrityError) as e:
                        print(f"Error processing row: {row}. Error: {str(e)}")
                        continue
                
                if saved_entries > 0:
                    messages.success(request, f"File uploaded successfully. {saved_entries} new entries saved.")
                elif skipped_duplicates:
                    messages.warning(request, f"The file contains {len(skipped_duplicates)} entries that already exist.")
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
        else:
            messages.error(request, "No file selected.")
    
        return redirect(f"{reverse('exapp:totalsolutions')}?category={category_filter}&search={search_query}")


@csrf_exempt
@login_required
def update_field(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            updates = data.get("updates", {})

            if not updates:
                return JsonResponse({"status": "error", "message": "No updates provided"}, status=400)

            updated_values = {}
            for row_id, fields in updates.items():
                obj = get_object_or_404(Totalsolutions, id=row_id)
                update_fields = []

                for field, value in fields.items():
                    if hasattr(obj, field):
                        field_type = obj._meta.get_field(field).get_internal_type()
                        if field_type in ["IntegerField", "PositiveIntegerField"]:
                            value = int(float(value or 0))
                        elif field_type in ["FloatField", "DecimalField"]:
                            value = float(value or 0)
                        elif field_type == "BooleanField":
                            value = value.lower() in ["true", "1"]
                        else:
                            value = str(value) if value is not None else None

                        if field in ['discount', 'buying_price', 'list_price']:
                            setattr(obj, field, value)
                            update_fields.extend(['sales_price', 'sales_margin', field])
                        else:
                            setattr(obj, field, value)
                            update_fields.append(field)

                obj.save(update_fields=update_fields)
                updated_values[row_id] = {
                    'discount': str(obj.discount),
                    'sales_price': str(obj.sales_price),
                    'sales_margin': str(obj.sales_margin),
                    'buying_price': str(obj.buying_price),
                    'buying_price_color': obj.buying_price_color
                }

            return JsonResponse({
                "status": "success",
                "message": "Fields updated successfully",
                "updated_values": updated_values
            })
        except Totalsolutions.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Item not found"}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON data"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Server error: {str(e)}"}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)


@csrf_exempt
@login_required
def upload_image(request, id):
    if request.method == 'POST':
        item = get_object_or_404(Totalsolutions, id=id)
        if 'product_image' in request.FILES:
            # Delete old image if it exists
            if item.product_image and os.path.isfile(item.product_image.path):
                os.remove(item.product_image.path)
            item.product_image = request.FILES['product_image']
            item.save()
            return JsonResponse({
                'success': True,
                'message': 'Image uploaded successfully.',
                'image_url': item.product_image.url
            })
        return JsonResponse({'success': False, 'message': 'No image file provided.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)


def boq(request):
    return render(request, 'boq.html', {})


def generate_token():
    return secrets.token_urlsafe()


def view_with_token(request):
    token = generate_token()
    request.session['access_token'] = token
    return render(request, 'login.html', {'token': token})


def validate_token(request):
    token = request.GET.get('token')
    session_token = request.session.get('access_token')
    if token != session_token:
        return HttpResponseForbidden("Invalid access.")
    return render(request, 'login.html')