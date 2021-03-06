from zerver.lib.actions import check_send_stream_message
from zerver.lib.response import json_success
from zerver.decorator import REQ, has_request_variables, api_key_only_webhook_view
from zerver.models import UserProfile

from django.http import HttpRequest, HttpResponse
from typing import Dict, Any, Optional, Text


GCI_MESSAGE_TEMPLATE = u'**{student}** {action} task [{task_name}]({task_url}).'
GCI_SUBJECT_TEMPLATE = u'Task: {task_name}'


class UnknownEventType(Exception):
    pass

def get_abandon_event_body(payload):
    # type: (Dict[Text, Any]) -> Text
    return GCI_MESSAGE_TEMPLATE.format(
        student=payload['task_claimed_by'],
        action='{}ed'.format(payload['type']),
        task_name=payload['task_definition_name'],
        task_url=payload['task_definition_url'],
    )


@api_key_only_webhook_view("Google-Code-In")
@has_request_variables
def api_gci_webhook(request, user_profile, stream=REQ(default='gci'),
                    payload=REQ(argument_type='body')):
    # type: (HttpRequest, UserProfile, Text, Dict[Text, Any]) -> HttpResponse
    event = get_event(payload)
    if event is not None:
        body = get_body_based_on_event(event)(payload)
        subject = GCI_SUBJECT_TEMPLATE.format(
            task_name=payload['task_definition_name']
        )
        check_send_stream_message(user_profile, request.client,
                                  stream, subject, body)

    return json_success()

EVENTS_FUNCTION_MAPPER = {
    'abandon': get_abandon_event_body,
}

def get_event(payload):
    # type: (Dict[Text, Any]) -> Optional[Text]
    event = payload['type']
    if event in EVENTS_FUNCTION_MAPPER:
        return event

    # TODO raise UnknownEventType as we support more events
    return None  # nocoverage

def get_body_based_on_event(event):
    # type: (Text) -> Any
    return EVENTS_FUNCTION_MAPPER[event]
