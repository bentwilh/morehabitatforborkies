import os
import uuid
from urllib.parse import urlencode

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
import openai

# Flask application setup
app = Flask(__name__)

# Azure Services
ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")
ACS_PHONE_NUMBER = os.getenv("ACS_PHONE_NUMBER")
TARGET_PHONE_NUMBER = "+4915204446662"
COGNITIVE_SERVICES_ENDPOINT = os.getenv("COGNITIVE_SERVICES_ENDPOINT")
AZURE_OPENAI_SERVICE_KEY = os.getenv("AZURE_OPENAI_SERVICES_KEY")
CALLBACK_EVENTS_URI = "https://morehabitatforborkies-production.up.railway.app/api/callbacks"
SPEECH_TO_TEXT_VOICE = "en-US-NancyNeural"
OUTGOING_MESSAGE = "Hello, this is a notification from wood watchers." \
            "We have detected potential environmental damage in your area of responsiblity." \
            "We kindly ask you to call back this number to give us an update once you have investigated the situation. Thank you."
call_automation_client = CallAutomationClient.from_connection_string(ACS_CONNECTION_STRING)
AZURE_OPENAI_DEPLOYMENT_MODEL = "gpt-3.5-turbo"
openai.api_key = AZURE_OPENAI_SERVICE_KEY


@app.route('/')
def hello_world():
    return "Hello World!"


app = Flask(__name__)


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


def handle_recognize(replyText, callerId, call_connection_id, context=""):
    play_source = TextSource(text=replyText, voice_name=SPEECH_TO_TEXT_VOICE)
    recognize_result = call_automation_client.get_call_connection(call_connection_id).start_recognizing_media(
        input_type=RecognizeInputType.SPEECH,
        target_participant=PhoneNumberIdentifier(callerId),
        end_silence_timeout=5,
        play_prompt=play_source,
        operation_context=context,
    )
    app.logger.info("handle_recognize : data=%s", recognize_result)


def handle_hangup(call_connection_id):
    call_automation_client.get_call_connection(call_connection_id).hang_up(is_for_everyone=True)


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

        if event.type == "Microsoft.Communication.CallConnected":
            app.logger.info("Starting recognize")
            handle_play(call_connection_client=call_connection_client,
                        text_to_play=OUTGOING_MESSAGE)

        # # Perform different actions based on DTMF tone received from RecognizeCompleted event
        # elif event.type == "Microsoft.Communication.RecognizeCompleted":
        #     app.logger.info("Recognize completed: data=%s", event.data)
        #     if event.data['recognitionType'] == "choices":
        #         label_detected = event.data['choiceResult']['label'];
        #         phraseDetected = event.data['choiceResult']['recognizedPhrase'];
        #         app.logger.info("Recognition completed, labelDetected=%s, phraseDetected=%s, context=%s",
        #                         label_detected, phraseDetected, event.data.get('operationContext'))
        #         if label_detected == CONFIRM_CHOICE_LABEL:
        #             text_to_play = CONFIRMED_TEXT
        #         else:
        #             text_to_play = CANCEL_TEXT
        #         handle_play(call_connection_client=call_connection_client, text_to_play=text_to_play)
        #
        # elif event.type == "Microsoft.Communication.RecognizeFailed":
        #     failedContext = event.data['operationContext']
        #     if (failedContext and failedContext == RETRY_CONTEXT):
        #         handle_play(call_connection_client=call_connection_client, text_to_play=NO_RESPONSE)
        #     else:
        #         resultInformation = event.data['resultInformation']
        #         app.logger.info("Encountered error during recognize, message=%s, code=%s, subCode=%s",
        #                         resultInformation['message'],
        #                         resultInformation['code'],
        #                         resultInformation['subCode'])
        #         if (resultInformation['subCode'] in [8510, 8510]):
        #             textToPlay = CUSTOMER_QUERY_TIMEOUT
        #         else:
        #             textToPlay = INVALID_AUDIO
        #
        #         get_media_recognize_choice_options(
        #             call_connection_client=call_connection_client,
        #             text_to_play=textToPlay,
        #             target_participant=target_participant,
        #             choices=get_choices(), context=RETRY_CONTEXT)

        elif event.type in ["Microsoft.Communication.PlayCompleted", "Microsoft.Communication.PlayFailed"]:
            app.logger.info("Terminating call")
            handle_hangup(call_connection_id)

        return Response(status=200)


@app.route("/api/callbacks/<contextId>", methods=["POST"])
def handle_callback(contextId):
    app.logger.info("RECEIVED CALL-IN CALLBACK")
    try:
        global caller_id, call_connection_id
        app.logger.info("Request Json: %s", request.json)
        for event_dict in request.json:
            event = CloudEvent.from_dict(event_dict)
            call_connection_id = event.data['callConnectionId']

            app.logger.info("%s event received for call connection id: %s", event.type, call_connection_id)
            caller_id = request.args.get("callerId").strip()
            if "+" not in caller_id:
                caller_id = "+" + caller_id.strip()

            app.logger.info("call connected : data=%s", event.data)
            if event.type == "Microsoft.Communication.CallConnected":
                handle_recognize("Hello! Thanks for calling back! Please let us know what you have found out about the incident.", caller_id, call_connection_id,
                                 context="GetFreeFormText")

            elif event.type == "Microsoft.Communication.RecognizeCompleted":
                if event.data['recognitionType'] == "speech":
                    speech_text = event.data['speechResult']['speech'];
                    app.logger.info("Recognition completed, speech_text =%s", speech_text)
                    if speech_text is not None and len(speech_text) > 0:
                        static_response = "Thank you for your input. One of our representatives will be in touch if further context or action should be required."
                        # if len(static_response) > 390:
                        #     static_response = static_response[:390]
                        handle_recognize(static_response, caller_id, call_connection_id, context="StaticResponse")

            elif event.type == "Microsoft.Communication.RecognizeFailed":
                resultInformation = event.data['resultInformation']
                reasonCode = resultInformation['subCode']
                context = event.data['operationContext']
                global max_retry
                if reasonCode == 8510 and 0 < max_retry:
                    handle_recognize("Please repeat that.", caller_id, call_connection_id)
                    max_retry -= 1
                else:
                    handle_play(call_connection_id, caller_id, "Have a wonderful day, goodbye!", "EndCall")

            elif event.type == "Microsoft.Communication.PlayCompleted":
                context = event.data['operationContext']
                if context.lower() == "endcall".lower():
                    handle_hangup(call_connection_id)

        return Response(status=200)
    except Exception as ex:
        app.logger.error("Error in event handling: %s", ex)


@app.route("/api/incomingCall", methods=['POST'])
def incoming_call_handler():
    app.logger.info("RECEIVED CALL")
    for event_dict in request.json:
        event = EventGridEvent.from_dict(event_dict)
        app.logger.info("incoming event data --> %s", event.data)
        if event.event_type == SystemEventNames.EventGridSubscriptionValidationEventName:
            app.logger.info("Validating subscription")
            validation_code = event.data['validationCode']
            validation_response = {'validationResponse': validation_code}
            return Response(response=json.dumps(validation_response), status=200)
        elif event.event_type == "Microsoft.Communication.IncomingCall":
            app.logger.info("Incoming call received: data=%s",
                            event.data)
            if event.data['from']['kind'] == "phoneNumber":
                caller_id = event.data['from']["phoneNumber"]["value"]
            else:
                caller_id = event.data['from']['rawId']
            app.logger.info("incoming call handler caller id: %s",
                            caller_id)
            incoming_call_context = event.data['incomingCallContext']
            guid = uuid.uuid4()
            query_parameters = urlencode({"callerId": caller_id})
            callback_uri = f"{CALLBACK_EVENTS_URI}/{guid}?{query_parameters}"

            app.logger.info("callback url: %s", callback_uri)

            answer_call_result = call_automation_client.answer_call(incoming_call_context=incoming_call_context,
                                                                    cognitive_services_endpoint=COGNITIVE_SERVICES_ENDPOINT,
                                                                    callback_url=callback_uri)
            app.logger.info("Answered call for connection id: %s",
                            answer_call_result.call_connection_id)
            return Response(status=200)


if __name__ == '__main__':
    app.logger.setLevel(INFO)
    app.run(host="0.0.0.0", debug=True, port=os.getenv("PORT", default=1234))
