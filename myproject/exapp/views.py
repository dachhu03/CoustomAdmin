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
    
    category_options = ['all', 'software', 'hardware', 'services']
    
    return render(request, 'totalsolutions.html', {
        'objs': products,
        'category_filter': category_filter,
        'search_query': search_query,
        'category_options': category_options
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
            'application': obj.application,
            'category': obj.category,
            'product_name': obj.product_name,
            'make': obj.make,
            'model': obj.model,
            'specification': obj.specification,
            'uom': obj.uom,
            'buying_price': float(obj.buying_price),
            'vendor': obj.vendor,
            'quotation_received_month': obj.quotation_received_month,
            'lead_time': obj.lead_time,
            'remarks': obj.remarks,
            'list_price': float(obj.list_price),
            'discount': int(obj.discount),
            'sales_price': float(obj.sales_price),
            'sales_margin': int(obj.sales_margin),
        } for obj in products
    ]
    
    return JsonResponse({'products': data})


@login_required
def additem(request):
    if request.method == 'POST':
        try:
            Totalsolutions.objects.create(
                application=request.POST.get('application'),
                category=request.POST.get('category'),
                product_name=request.POST.get('product_name'),
                make=request.POST.get('make'),
                model=request.POST.get('model'),
                specification=request.POST.get('specification'),
                uom=request.POST.get('uom'),
                buying_price=float(request.POST.get('buying_price', 0)),
                vendor=request.POST.get('vendor'),
                quotation_received_month=request.POST.get('quotation_received_month'),
                lead_time=request.POST.get('lead_time'),
                remarks=request.POST.get('remarks'),
                list_price=float(request.POST.get('list_price', 0)),
                discount=int(float(request.POST.get('discount', 0))),
                sales_price=float(request.POST.get('sales_price', 0)),
                sales_margin=int(float(request.POST.get('sales_margin', 0))),
            )
            messages.success(request, "Item added successfully.")
        except (ValueError, IntegrityError) as e:
            messages.error(request, f"Error adding item: {str(e)}")
        return redirect('exapp:totalsolutions')
    return render(request, 'totalsolutions.html')


@login_required
def delete_all(request):
    if request.method == 'POST':
        Totalsolutions.objects.all().delete()
        messages.success(request, 'All items have been deleted successfully.')
    return redirect('exapp:totalsolutions')


@login_required
def delete(request, id):
    item = get_object_or_404(Totalsolutions, id=id)
    if request.method == 'POST':
        item_name = str(item)
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
                elif field == 'discount':
                    value = int(float(value.replace('%', '')))
                    list_price = float(item.list_price)
                    sales_price = max(list_price - (list_price * value / 100), 0)
                    buying_price = float(item.buying_price)
                    sales_margin = int((sales_price - buying_price) / sales_price * 100) if sales_price > 0 else 0
                    item.sales_price = sales_price
                    item.sales_margin = sales_margin
                elif field == 'sales_margin':
                    value = int(float(value))

                setattr(item, field, value)
                item.save()

                return JsonResponse({
                    'success': True,
                    'message': f'{field} updated successfully.',
                    'sales_price': item.sales_price,
                    'sales_margin': item.sales_margin
                })
            else:
                return JsonResponse({'success': False, 'message': 'Invalid field.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    if request.method == 'POST':
        try:
            list_price = max(float(request.POST.get('list_price', 0)), 0)
            discount_value = request.POST.get('discount', '0').replace('%', '')
            discount = int(float(discount_value)) if discount_value else 0
            buying_price = max(float(request.POST.get('buying_price', 0)), 0)
            sales_price = max(list_price - (list_price * discount / 100), 0)
            sales_margin = int((sales_price - buying_price) / sales_price * 100) if sales_price > 0 else 0

            item.application = request.POST.get('application')
            item.category = request.POST.get('category')
            item.product_name = request.POST.get('product_name')
            item.make = request.POST.get('make')
            item.model = request.POST.get('model')
            item.specification = request.POST.get('specification')
            item.uom = request.POST.get('uom')
            item.buying_price = buying_price
            item.vendor = request.POST.get('vendor')
            item.quotation_received_month = request.POST.get('quotation_received_month')
            item.lead_time = request.POST.get('lead_time')
            item.remarks = request.POST.get('remarks')
            item.list_price = list_price
            item.discount = discount
            item.sales_price = sales_price
            item.sales_margin = sales_margin
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
                    df = pd.read_csv(file)
                elif file.name.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(file)
                else:
                    raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")
                
                df['category'] = df['category'].str.strip().str.lower()

                required_columns = [
                    'application', 'category', 'product_name', 'make', 'model', 'specification',
                    'uom', 'buying_price', 'vendor', 'quotation_received_month',
                    'lead_time', 'remarks', 'list_price', 'discount', 'sales_price', 'sales_margin'
                ]
                missing_columns = set(required_columns) - set(df.columns)
                if missing_columns:
                    raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
                
                if category_filter != 'all' and category_filter in ['software', 'hardware', 'services']:
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
                            row_dict['discount'] = int(float(row_dict.get('discount', 0)))
                            row_dict['sales_margin'] = int(float(row_dict.get('sales_margin', 0)))
                            Totalsolutions.objects.create(**row_dict)
                            saved_entries += 1
                        else:
                            skipped_duplicates.append(row.to_dict())
                    except (ValueError, IntegrityError) as e:
                        print(f"Error processing row: {row}. Error: {str(e)}")
                        continue
                
                if saved_entries > 0:
                    messages.success(request, f"File uploaded successfully. {saved_entries} new entries saved.")
                elif skipped_duplicates:
                    messages.warning(request, f"The file contains {len(skipped_duplicates)} entries that already exist. No new entries were added.")
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
                            value = str(value) if value is not None else ""

                        if field == 'discount':
                            discount = value
                            list_price = float(obj.list_price or 0)
                            sales_price = max(list_price - (list_price * discount / 100), 0)
                            buying_price = float(obj.buying_price or 0)
                            sales_margin = int((sales_price - buying_price) / sales_price * 100) if sales_price > 0 else 0
                            obj.discount = discount  # Fixed typo here
                            obj.sales_price = sales_price
                            obj.sales_margin = sales_margin
                            update_fields.extend(['discount', 'sales_price', 'sales_margin'])
                        elif field == 'buying_price':
                            buying_price = value
                            list_price = float(obj.list_price or 0)
                            discount = float(obj.discount or 0)
                            sales_price = max(list_price - (list_price * discount / 100), 0)
                            sales_margin = int((sales_price - buying_price) / sales_price * 100) if sales_price > 0 else 0
                            obj.buying_price = buying_price
                            obj.sales_price = sales_price
                            obj.sales_margin = sales_margin
                            update_fields.extend(['buying_price', 'sales_price', 'sales_margin'])
                        else:
                            setattr(obj, field, value)
                            update_fields.append(field)

                obj.save(update_fields=update_fields)
                updated_values[row_id] = {
                    'discount': str(obj.discount),
                    'sales_price': str(obj.sales_price),
                    'sales_margin': str(obj.sales_margin),
                    'buying_price': str(obj.buying_price)
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