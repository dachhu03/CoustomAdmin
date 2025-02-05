from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse ,  HttpResponseForbidden
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
        # "total_sales_price": total_sales_price,
        # "top_vendors": top_vendors,
        # "monthly_sales": monthly_sales,
    }
    return render(request, "home.html", context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('exapp:home')  # Redirect to home page
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')
@login_required
def totalsolutions(request):
    # Get search query parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', 'all')
    
    # Filter the products based on the search query and category
    products = Totalsolutions.objects.all()
    
    if search_query:
        products = products.filter(application__icontains=search_query)
    
    if category_filter != 'all':
        products = products.filter(category=category_filter)
    
    return render(request, 'totalsolutions.html', {
        'objs': products,
        'category_filter': category_filter,
        'search_query': search_query
    })

@login_required
def additem(request):
    if request.method == 'POST':
        # Create the item and save it
        Totalsolutions.objects.create(
            application=request.POST.get('application'),
            category=request.POST.get('category'),
            product_name=request.POST.get('product_name'),
            make=request.POST.get('make'),
            model=request.POST.get('model'),
            specification=request.POST.get('specification'),
            uom=request.POST.get('uom'),
            buying_price=request.POST.get('buying_price'),
            vendor=request.POST.get('vendor'),
            quotation_received_month=request.POST.get('quotation_received_month'),
            lead_time=request.POST.get('lead_time'),
            remarks=request.POST.get('remarks'),
            list_price=request.POST.get('list_price'),
            discount=request.POST.get('discount'),
            sales_price=request.POST.get('sales_price'),
            sales_margin=request.POST.get('sales_margin'),
        )
        return redirect('exapp:totalsolutions')
    return render(request, 'totalsolutions.html')

@login_required
def delete(request, id):
    item = get_object_or_404(Totalsolutions, id=id)

    if request.method == 'POST':
        item_name = str(item)  # Get the name or representation of the item for the message
        item.delete()
        messages.success(request, f'The item "{item_name}" has been successfully deleted.')
        return redirect('exapp:totalsolutions')
    
    return render(request, 'totalsolutions.html', {'item': item})

@login_required
def edit(request, id):
    item = get_object_or_404(Totalsolutions, id=id)

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Handle AJAX request
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
                # Validate and update the field
                if field == 'list_price':
                    value = max(float(value), 0)  # Ensure list_price is non-negative
                elif field == 'discount':
                    value = value.replace('%', '') if isinstance(value, str) and '%' in value else value
                    discount = max(float(value) / 100, 0)  # Convert to decimal and ensure non-negative
                    value = discount * 100  # Store discount as a percentage

                    # Recalculate sales_price and sales_margin
                    list_price = item.list_price
                    sales_price = max(list_price - (list_price * discount), 0)  # Ensure non-negative sales_price
                    buying_price = item.buying_price
                    sales_margin = (sales_price - buying_price) / sales_price if sales_price > 0 else 0

                    item.sales_price = sales_price
                    item.sales_margin = sales_margin

                setattr(item, field, value)
                item.save()

                return JsonResponse({'success': True, 'message': f'{field} updated successfully.'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid field.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    if request.method == 'POST':
        # Handle regular form submissions
        try:
            # Validate and get inputs
            list_price = max(float(request.POST.get('list_price', 0)), 0)
            discount_value = request.POST.get('discount', '0').replace('%', '')

            try:
                discount = max(float(discount_value) / 100, 0)  # Convert to decimal and ensure non-negative
            except ValueError:
                discount = 0  # Default to 0 if invalid

            buying_price = max(float(request.POST.get('buying_price', 0)), 0)

            # Calculate sales price and margin
            sales_price = max(list_price - (list_price * discount), 0)
            sales_margin = (sales_price - buying_price) / sales_price if sales_price > 0 else 0

            # Update item fields
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
            item.discount = discount * 100  # Store discount as percentage
            item.sales_price = sales_price
            item.sales_margin = sales_margin
            item.save()

            # Add success message
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
        if file:
            try:
                # Check file extension
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                elif file.name.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(file)
                else:
                    raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")
                
                # Clean the category column
                df['category'] = df['category'].str.strip().str.lower()

                # Validate required columns
                required_columns = [
                    'application', 'category', 'product_name', 'make', 'model', 'specification',
                    'uom', 'buying_price', 'vendor', 'quotation_received_month',
                    'lead_time', 'remarks', 'list_price', 'discount', 'sales_price', 'sales_margin'
                ]
                missing_columns = set(required_columns) - set(df.columns)
                if missing_columns:
                    raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
                
                # Filter the DataFrame based on the category_filter
                if category_filter != 'all' and category_filter in ['software', 'hardware', 'services']:
                    df = df[df['category'] == category_filter.lower()]
                
                # Track skipped and saved rows
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
                            Totalsolutions.objects.create(**row.to_dict())
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

@login_required
def update_row(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            row_id = data.get('row_id')
            field = data.get('field')
            value = data.get('value')

            # Validate row_id and field
            obj = Totalsolutions.objects.get(pk=row_id)
            if not hasattr(obj, field):
                return JsonResponse({'success': False, 'error': f"Field {field} does not exist on Totalsolutions"})

            setattr(obj, field, value)  # Update field
            obj.save()
            return JsonResponse({'success': True})
        except Totalsolutions.DoesNotExist:
            return JsonResponse({'success': False, 'error': f"Totalsolutions object with ID {row_id} does not exist"})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

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


