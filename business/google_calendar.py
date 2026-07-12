import datetime
import logging
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar.events']


def get_flow(request, business):
    from google_auth_oauthlib.flow import Flow
    flow = Flow.from_client_config(
        settings.GOOGLE_OAUTH_CLIENT_CONFIG,
        scopes=SCOPES,
        state=str(business.pk),
    )
    flow.redirect_uri = request.build_absolute_uri(
        reverse('business:google_calendar_callback')
    )
    return flow


def get_service(credentials_dict):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_authorized_user_info(credentials_dict, SCOPES)
    return build('calendar', 'v3', credentials=creds)


def create_event(credentials_dict, calendar_id, appointment):
    if not credentials_dict:
        return None
    try:
        service = get_service(credentials_dict)
        start_dt = datetime.datetime.combine(
            appointment.date,
            appointment.time or datetime.time(9, 0),
        )
        end_dt = start_dt + datetime.timedelta(hours=1)
        event = {
            'summary': f"{appointment.customer.full_name} — {appointment.service.name if appointment.service else 'Qabul'}",
            'description': (
                f"Mijoz: {appointment.customer.full_name}\n"
                f"Tel: {appointment.customer.phone}\n"
                f"Xizmat: {appointment.service.name if appointment.service else '—'}\n"
                f"Xodim: {appointment.employee.name if appointment.employee else '—'}\n"
                f"Holat: {appointment.get_status_display()}"
            ),
            'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Asia/Tashkent'},
            'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Asia/Tashkent'},
        }
        created = service.events().insert(calendarId=calendar_id, body=event).execute()
        return created.get('id')
    except Exception as e:
        logger.error(f'Google Calendar create_event error: {e}')
        return None


def update_event(credentials_dict, calendar_id, event_id, appointment):
    if not credentials_dict or not event_id:
        return False
    try:
        service = get_service(credentials_dict)
        start_dt = datetime.datetime.combine(
            appointment.date,
            appointment.time or datetime.time(9, 0),
        )
        end_dt = start_dt + datetime.timedelta(hours=1)
        event = {
            'summary': f"{appointment.customer.full_name} — {appointment.service.name if appointment.service else 'Qabul'}",
            'description': (
                f"Mijoz: {appointment.customer.full_name}\n"
                f"Tel: {appointment.customer.phone}\n"
                f"Xizmat: {appointment.service.name if appointment.service else '—'}\n"
                f"Xodim: {appointment.employee.name if appointment.employee else '—'}\n"
                f"Holat: {appointment.get_status_display()}"
            ),
            'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Asia/Tashkent'},
            'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Asia/Tashkent'},
        }
        service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
        return True
    except Exception as e:
        logger.error(f'Google Calendar update_event error: {e}')
        return False


def delete_event(credentials_dict, calendar_id, event_id):
    if not credentials_dict or not event_id:
        return False
    try:
        service = get_service(credentials_dict)
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return True
    except Exception as e:
        logger.error(f'Google Calendar delete_event error: {e}')
        return False
