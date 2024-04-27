import os

from azure.eventgrid import EventGridEvent, SystemEventNames
from flask import Flask, Response, request, json, send_file, render_template, redirect
from logging import INFO
from azure.communication.callautomation import (
    CallAutomationClient,
    CallConnectionClient,
    PhoneNumberIdentifier,
    RecognizeInputType,
    MicrosoftTeamsUserIdentifier,
    CallInvite,
    RecognitionChoice,
    DtmfTone,
    TextSource)
from azure.core.messaging import CloudEvent
from azure.communication.sms import SmsClient


# Flask application setup
app = Flask(__name__)

# Your ACS resource connection string, source and target phone numbers
ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")
ACS_PHONE_NUMBER = os.getenv("ACS_PHONE_NUMBER")
TARGET_PHONE_NUMBER = "+4915204446662"
COGNITIVE_SERVICES_ENDPOINT = os.getenv("COGNITIVE_SERVICES_ENDPOINT")
AZURE_OPENAI_SERVICE_KEY = os.getenv("AZURE_OPENAI_SERVICES_KEY")

# Callback URI to handle events.
CALLBACK_EVENTS_URI = "https://morehabitatforborkies-production.up.railway.app/api/callbacks"

# Text-to-speech voice and initial announcement text
SPEECH_TO_TEXT_VOICE = "en-US-NancyNeural"
MAIN_MENU = "Hello, this is notification from wood watchers. We have detected potential environmental damage in your area of responsiblity. Do you want to receive a summary notification via SMS?"
CONFIRMED_TEXT = "Thank you, a summary SMS has been sent."
CANCEL_TEXT = "Alright, I won't send an SMS then. Thank you."
CUSTOMER_QUERY_TIMEOUT = "I’m sorry I didn’t receive a response, please try again."
NO_RESPONSE = "I didn't receive an input, we will go ahead and send an SMS. Goodbye"
INVALID_AUDIO = "I’m sorry, I didn’t understand your response, please try again."
CONFIRM_CHOICE_LABEL = "Confirm"
CANCEL_CHOICE_LABEL = "Cancel"
RETRY_CONTEXT = "retry"

# Create the call automation client
call_automation_client = CallAutomationClient.from_connection_string(ACS_CONNECTION_STRING)


@app.route('/')
def hello_world():
    return "Hello World!"


app = Flask(__name__)


def get_choices():
    choices = [
        RecognitionChoice(label=CONFIRM_CHOICE_LABEL, phrases=["Confirm", "First", "One", "Yes"], tone=DtmfTone.ONE),
        RecognitionChoice(label=CANCEL_CHOICE_LABEL, phrases=["Cancel", "Second", "Two", "No"], tone=DtmfTone.TWO)
    ]
    return choices


def get_media_recognize_choice_options(call_connection_client: CallConnectionClient, text_to_play: str,
                                       target_participant: str, choices: any, context: str):
    play_source = TextSource(text=text_to_play, voice_name=SPEECH_TO_TEXT_VOICE)
    call_connection_client.start_recognizing_media(
        input_type=RecognizeInputType.CHOICES,
        target_participant=target_participant,
        choices=choices,
        play_prompt=play_source,
        interrupt_prompt=False,
        initial_silence_timeout=10,
        operation_context=context
    )


def handle_play(call_connection_client: CallConnectionClient, text_to_play: str):
    play_source = TextSource(text=text_to_play, voice_name=SPEECH_TO_TEXT_VOICE)
    call_connection_client.play_media_to_all(play_source)


# GET endpoint to place phone call
@app.route('/outboundCall')
def outbound_call_handler():
    target_participant = PhoneNumberIdentifier(TARGET_PHONE_NUMBER)
    source_caller = PhoneNumberIdentifier(ACS_PHONE_NUMBER)
    call_connection_properties = call_automation_client.create_call(target_participant=target_participant,
                                                                    callback_url=CALLBACK_EVENTS_URI,
                                                                    cognitive_services_endpoint=COGNITIVE_SERVICES_ENDPOINT,
                                                                    source_caller_id_number=source_caller)
    app.logger.info("Created call with connection id: %s", call_connection_properties.call_connection_id)
    return Response(status=200)


# POST endpoint to handle callback events
@app.route('/api/callbacks', methods=['POST'])
def callback_events_handler():
    for event_dict in request.json:
        # Parsing callback events
        event = CloudEvent.from_dict(event_dict)
        call_connection_id = event.data['callConnectionId']
        app.logger.info("%s event received for call connection id: %s", event.type, call_connection_id)
        call_connection_client = call_automation_client.get_call_connection(call_connection_id)
        target_participant = PhoneNumberIdentifier(TARGET_PHONE_NUMBER)
        if event.type == "Microsoft.Communication.CallConnected":
            app.logger.info("Starting recognize")
            get_media_recognize_choice_options(
                call_connection_client=call_connection_client,
                text_to_play=MAIN_MENU,
                target_participant=target_participant,
                choices=get_choices(), context="")

        # Perform different actions based on DTMF tone received from RecognizeCompleted event
        elif event.type == "Microsoft.Communication.RecognizeCompleted":
            app.logger.info("Recognize completed: data=%s", event.data)
            if event.data['recognitionType'] == "choices":
                label_detected = event.data['choiceResult']['label'];
                phraseDetected = event.data['choiceResult']['recognizedPhrase'];
                app.logger.info("Recognition completed, labelDetected=%s, phraseDetected=%s, context=%s",
                                label_detected, phraseDetected, event.data.get('operationContext'))
                if label_detected == CONFIRM_CHOICE_LABEL:
                    text_to_play = CONFIRMED_TEXT
                    send_sms()
                else:
                    text_to_play = CANCEL_TEXT
                handle_play(call_connection_client=call_connection_client, text_to_play=text_to_play)

        elif event.type == "Microsoft.Communication.RecognizeFailed":
            failedContext = event.data['operationContext']
            if (failedContext and failedContext == RETRY_CONTEXT):
                handle_play(call_connection_client=call_connection_client, text_to_play=NO_RESPONSE)
                send_sms()
            else:
                resultInformation = event.data['resultInformation']
                app.logger.info("Encountered error during recognize, message=%s, code=%s, subCode=%s",
                                resultInformation['message'],
                                resultInformation['code'],
                                resultInformation['subCode'])
                if (resultInformation['subCode'] in [8510, 8510]):
                    textToPlay = CUSTOMER_QUERY_TIMEOUT
                else:
                    textToPlay = INVALID_AUDIO

                get_media_recognize_choice_options(
                    call_connection_client=call_connection_client,
                    text_to_play=textToPlay,
                    target_participant=target_participant,
                    choices=get_choices(), context=RETRY_CONTEXT)

        elif event.type in ["Microsoft.Communication.PlayCompleted", "Microsoft.Communication.PlayFailed"]:
            app.logger.info("Terminating call")
            call_connection_client.hang_up(is_for_everyone=True)

        return Response(status=200)


def send_sms():
    print("sending SMS")
    sms_client = SmsClient.from_connection_string(ACS_CONNECTION_STRING)
    sms_responses = sms_client.send(
        from_=ACS_PHONE_NUMBER,
        to=[TARGET_PHONE_NUMBER],
        message="Map Details will go here")


if __name__ == '__main__':
    app.logger.setLevel(INFO)
    app.run(host="0.0.0.0", debug=True, port=os.getenv("PORT", default=1234))
