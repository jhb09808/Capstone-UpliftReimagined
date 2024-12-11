from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from .forms import CustomUserCreationForm, EditProfileForm
from .models import Volunteer, InventoryItem, Shift, CustomUser, ShiftHistory
import requests
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
import logging
from django.utils import timezone
from .models import VolunteerLog
from django.db.models import Sum
from datetime import timedelta


def admin_check(user):
    return user.is_staff

@user_passes_test(admin_check)
def manage_users(request):
    if not request.user.is_staff:
        return redirect('home')

    users = CustomUser.objects.all()
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user = CustomUser.objects.get(id=user_id)
        if action == 'deactivate':
            user.is_active = False
        elif action == 'activate':
            user.is_active = True
        elif action == 'make_admin':
            user.is_staff = True
        user.save()
        return redirect('manage_users')

    return render(request, 'uplift/manage_users.html', {'users': users})

@user_passes_test(admin_check)
def manage_inventory(request):
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            item_name = request.POST.get('item_name')
            quantity = request.POST.get('quantity')
            category = request.POST.get('category')
            notes = request.POST.get('notes')
            InventoryItem.objects.create(name=item_name, quantity=quantity, category=category, notes=notes)
        elif action == 'update':
            item_id = request.POST.get('item_id')
            item = InventoryItem.objects.get(id=item_id)
            item.name = request.POST.get('item_name')
            item.quantity = request.POST.get('quantity')
            item.category = request.POST.get('category')
            item.notes = request.POST.get('notes')
            item.save()
        elif action == 'delete':
            item_id = request.POST.get('item_id')
            InventoryItem.objects.get(id=item_id).delete()
        return redirect('manage_inventory')

    inventory_items = InventoryItem.objects.all()
    return render(request, 'uplift/manage_inventory.html', {'inventory_items': inventory_items})

@user_passes_test(admin_check)
def confirm_shifts(request):
    if not request.user.is_staff:
        return redirect('home')

    if request.method == 'POST':
        shift_id = request.POST.get('shift_id')
        action = request.POST.get('action')
        try:
            shift = Shift.objects.get(id=shift_id)
            # Store volunteer info before any changes
            volunteer = shift.volunteer

            if action == 'approve':
                shift.status = 'approved'
                message = 'Shift approved successfully'
                activity = 'Approved'
            elif action == 'reject':
                shift.status = 'available'
                message = 'Shift rejected successfully'
                activity = 'Rejected'
            elif action == 'approve cancellation':
                shift.status = 'cancelled'
                message = 'Cancellation approved successfully'
                activity = 'Cancelled'
            elif action == 'reject cancellation':
                shift.status = 'approved'
                message = 'Cancellation rejected successfully'
                activity = 'Cancellation Rejected'

            # Create history record before modifying volunteer
            ShiftHistory.objects.create(
                shift=shift,
                volunteer=volunteer,  # Use stored volunteer
                description=shift.description,
                activity=activity,
                timestamp=timezone.now()
            )

            # Now update volunteer if needed
            if action in ['reject', 'approve cancellation']:
                shift.volunteer = None

            shift.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': message
                })
            return redirect('confirm_shifts')

        except Shift.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Shift not found'
                }, status=404)
            return redirect('confirm_shifts')

    pending_shifts = Shift.objects.filter(status='pending')
    pending_cancellations = Shift.objects.filter(status='cancellation pending')
    shift_history = ShiftHistory.objects.select_related('volunteer').order_by('-timestamp')

    return render(request, 'uplift/confirm_shifts.html', {
        'pending_shifts': pending_shifts,
        'pending_cancellations': pending_cancellations,
        'shift_history': shift_history
    })

@user_passes_test(admin_check)
def generate_reports(request):
    if not request.user.is_staff:
        return redirect('home')

    # Volunteer Activities
    year = request.GET.get('volunteer_year')
    month = request.GET.get('volunteer_month')
    volunteer_activities = Shift.objects.filter(volunteer__isnull=False).order_by('start_time')
    if year:
        volunteer_activities = volunteer_activities.filter(start_time__year=year)
    if month:
        volunteer_activities = volunteer_activities.filter(start_time__month=month)

    # User Registrations
    user_year = request.GET.get('user_year')
    user_month = request.GET.get('user_month')
    users = CustomUser.objects.all().order_by('-date_joined')
    if user_year:
        users = users.filter(date_joined__year=user_year)
    if user_month:
        users = users.filter(date_joined__month=user_month)

    # Inventory Items
    inventory_year = request.GET.get('inventory_year')
    inventory_month = request.GET.get('inventory_month')
    inventory_items = InventoryItem.objects.all().order_by('date_added')
    if inventory_year:
        inventory_items = inventory_items.filter(date_added__year=inventory_year)
    if inventory_month:
        inventory_items = inventory_items.filter(date_added__month=inventory_month)

    context = {
        'volunteer_activities': volunteer_activities,
        'users': users,
        'inventory_items': inventory_items,
        'years': range(datetime.now().year, 2020, -1),  # Adjust the range as needed
        'months': range(1, 13),
        'selected_volunteer_year': year,
        'selected_volunteer_month': month,
        'selected_user_year': user_year,
        'selected_user_month': user_month,
        'selected_inventory_year': inventory_year,
        'selected_inventory_month': inventory_month,
    }

    return render(request, 'uplift/generate_reports.html', context)

@login_required
def volunteer_list(request):
    volunteers = Volunteer.objects.all()
    return render(request, 'uplift/volunteer_list.html', {'volunteers': volunteers})

@login_required
def dashboard(request):
    is_admin = request.user.is_staff
    shifts = Shift.objects.all() if is_admin else Shift.objects.filter(volunteer=request.user)
    context = {
        'is_admin': is_admin,
        'shifts': shifts,
    }
    return render(request, 'uplift/dashboard.html', context)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def donate(request):
    return render(request, 'uplift/donate.html')

def route(request):
    return render(request, 'uplift/route.html')

def profile(request):
    if request.method == 'POST':
        if 'delete_account' in request.POST:
            user = request.user
            user.delete()
            messages.success(request, 'Your account has been successfully deleted.')
            return redirect('home')
        else:
            form = EditProfileForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your profile has been updated.')
                return redirect('profile')
    else:
        form = EditProfileForm(instance=request.user)

    # Get volunteer logs
    volunteer_logs = VolunteerLog.objects.filter(user=request.user).order_by('-date')

    # Calculate total hours from VolunteerLog
    total_hours_logs = VolunteerLog.objects.filter(user=request.user).aggregate(Sum('hours'))['hours__sum'] or 0
    total_hours_logs_td = timedelta(hours=total_hours_logs)

    # Get and process approved Shifts
    approved_shifts = Shift.objects.filter(volunteer=request.user, status='approved').order_by('-start_time')
    total_hours_shifts = timedelta()
    shift_logs = []

    for shift in approved_shifts:
        duration = shift.end_time - shift.start_time
        # Convert to 1.50 format instead of 1.83
        hours = duration.total_seconds() // 3600 + (duration.total_seconds() % 3600) / 60 / 100
        total_hours_shifts += duration

        # Convert UTC times to local timezone
        local_start = timezone.localtime(shift.start_time)
        local_end = timezone.localtime(shift.end_time)

        shift_logs.append({
            'date': shift.start_time.date(),
            'activity': shift.description,
            'start_time': local_start.strftime('%I:%M %p'),
            'end_time': local_end.strftime('%I:%M %p'),
            'hours': f"{hours:.2f}"
        })

    # Combine volunteer_logs and shift_logs
    combined_logs = list(volunteer_logs) + shift_logs
    combined_logs.sort(key=lambda x: x['date'], reverse=True)

    # Sum up total hours from logs and shifts
    total_hours = total_hours_logs_td + total_hours_shifts

    # Format total hours to HH:MM
    def format_total_hours(td):
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}:{minutes:02d}"

    is_admin = request.user.is_staff

    context = {
        'form': form,
        'is_admin': is_admin,
        'volunteer_logs': combined_logs,
        'total_hours': format_total_hours(total_hours),
    }

    return render(request, 'uplift/profile.html', context)

def home(request):
    return render(request, 'home.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'uplift/edit_profile.html', {'form': form})

def view_inventory(request):
    inventory_items = InventoryItem.objects.all()
    return render(request, 'inventory.html', {'inventory_items': inventory_items})

@login_required
def view_shift_schedule(request):
    user_shifts = Shift.objects.filter(volunteer=request.user, status='approved')
    if request.method == 'POST':
        shift_id = request.POST.get('shift_id')
        action = request.POST.get('action')
        shift = Shift.objects.get(id=shift_id)
        if action == 'cancel':
            shift.status = 'pending cancellation'
            shift.save()
            return redirect('view_shift_schedule')
    return render(request, 'shift_schedule.html', {'user_shifts': user_shifts})

def apply_for_shift(request):
    if request.method == 'POST':
        try:
            # Convert string timestamps to datetime objects and make them timezone-aware
            start_time = datetime.fromisoformat(request.POST.get('shiftStartTime'))
            end_time = datetime.fromisoformat(request.POST.get('shiftEndTime'))

            # Make the datetime objects timezone-aware
            start_time = timezone.make_aware(start_time)
            end_time = timezone.make_aware(end_time)
            description = request.POST.get('shiftDescription')

            # Get current time (already timezone-aware)
            current_time = timezone.now()

            # Now all datetime objects are timezone-aware
            if not (start_time and end_time and description):
                return JsonResponse({
                    'message': 'All fields are required.',
                    'success': False
                }, status=400)

            if start_time < current_time:
                return JsonResponse({
                    'message': 'Cannot create shifts for past dates.',
                    'success': False
                }, status=400)

            shift = Shift.objects.create(
                start_time=start_time,
                end_time=end_time,
                description=description,
                volunteer=request.user,
                status='pending'
            )

            return JsonResponse({
                'message': 'Your shift has been submitted for approval',
                'success': True,
                'shift': {
                    'id': shift.id,
                    'start': shift.start_time.isoformat(),
                    'end': shift.end_time.isoformat(),
                    'description': shift.description,
                    'status': shift.status
                }
            })

        except ValueError as e:
            return JsonResponse({
                'message': 'Invalid date format',
                'success': False
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'message': f'Error creating shift: {str(e)}',
                'success': False
            }, status=400)

    return JsonResponse({
        'message': 'Only POST method is allowed.',
        'success': False
    }, status=405)

@login_required
def get_shifts(request):
    user_shifts = Shift.objects.filter(volunteer=request.user).order_by('-start_time')
    shifts_data = []
    for shift in user_shifts:
        shifts_data.append({
            'id': shift.id,
            'start': shift.start_time.isoformat(),
            'end': shift.end_time.isoformat(),
            'description': shift.description,
            'status': shift.status
        })
    return JsonResponse({'shifts': shifts_data})

@login_required
def get_volunteers(request):
    date = request.GET.get('date')
    selected_day_shifts = Shift.objects.filter(start_time__date=date, volunteer__isnull=False)
    volunteers = [{'name': shift.volunteer.username} for shift in selected_day_shifts]
    return JsonResponse({'volunteers': volunteers})


@csrf_exempt
def proxy(request, path):
    url = f'https://unpkg.com/ionicons@5.5.2/dist/ionicons/{path}'
    response = requests.get(url)
    http_response = HttpResponse(response.content, content_type=response.headers['Content-Type'])
    http_response['Access-Control-Allow-Origin'] = '*'
    return http_response

def about(request):
    return render(request, 'uplift/about.html')

def contact(request):
    return render(request, 'uplift/contact.html')

def edit_shift(request, shift_id):
    if request.method == 'POST':
        try:
            shift = get_object_or_404(Shift, id=shift_id, volunteer=request.user)

            # Get updated values from request
            start_time = datetime.fromisoformat(request.POST.get('shiftStartTime'))
            end_time = datetime.fromisoformat(request.POST.get('shiftEndTime'))
            description = request.POST.get('shiftDescription')

            # Update shift object
            shift.start_time = start_time
            shift.end_time = end_time
            shift.description = description
            shift.status = 'pending'  # Reset status after edit
            shift.save()

            return JsonResponse({
                'success': True,
                'message': 'Shift updated successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error updating shift: {str(e)}'
            }, status=400)
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

def cancel_shift(request, shift_id):
    if request.method == 'POST':
        try:
            shift = get_object_or_404(Shift, id=shift_id, volunteer=request.user)
            if shift.status == 'approved':
                shift.status = 'cancellation pending'
                shift.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Shift cancellation request submitted successfully'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Only approved shifts can be cancelled'
                }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error cancelling shift: {str(e)}'
            }, status=400)
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)

@require_POST
def delete_user(request, user_id):
    print(f"Attempting to delete user {user_id}")
    if not request.user.is_superuser:
        print("Permission denied")
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    try:
        user = CustomUser.objects.get(id=user_id)
        print(f"Found user: {user.username}")
        if not user.is_superuser:
            user.delete()
            print("User deleted")
            return JsonResponse({'success': True})
        print("Cannot delete superuser")
        return JsonResponse({'success': False, 'message': 'Cannot delete superuser'})
    except CustomUser.DoesNotExist:
        print("User not found")
        return JsonResponse({'success': False, 'message': 'User not found'})

@require_POST
def activate_user(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    try:
        user = CustomUser.objects.get(id=user_id)
        user.is_active = True
        user.save()
        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'})

@require_POST
def deactivate_user(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    try:
        user = CustomUser.objects.get(id=user_id)
        if not user.is_superuser:
            user.is_active = False
            user.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'message': 'Cannot deactivate superuser'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'})

@require_POST
def make_admin(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    try:
        user = CustomUser.objects.get(id=user_id)
        user.is_staff = True
        user.save()
        return JsonResponse({'success': True})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'})

@require_POST
def remove_admin(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    try:
        user = CustomUser.objects.get(id=user_id)
        if not user.is_superuser:
            user.is_staff = False
            user.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'message': 'Cannot remove superuser admin status'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found'})

logger = logging.getLogger(__name__)


@user_passes_test(admin_check)
def update_inventory_item(request, item_id):
    if request.method == 'POST':
        item = InventoryItem.objects.get(id=item_id)
        item.name = request.POST.get('name')
        item.quantity = request.POST.get('quantity')
        item.category = request.POST.get('category')
        item.notes = request.POST.get('notes')
        item.save()
        return JsonResponse({
            'success': True,
            'message': 'Item updated successfully',
            'name': item.name,
            'category': item.category,
            'quantity': item.quantity,
            'date_updated': item.date_updated.strftime("%Y-%m-d %H:%M")
        })
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@user_passes_test(admin_check)
def delete_inventory_item(request, item_id):
    if request.method == 'POST':
        item = InventoryItem.objects.get(id=item_id)
        item.delete()
        return JsonResponse({'success': True, 'message': 'Item deleted successfully'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@require_POST
def delete_shift(request, shift_id):
    try:
        shift = Shift.objects.get(id=shift_id, volunteer=request.user, status='pending')
        shift.delete()
        return JsonResponse({'success': True, 'message': 'Shift deleted successfully'})
    except Shift.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Shift not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)