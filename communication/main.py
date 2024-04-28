import os
import uuid
from datetime import datetime
from urllib.parse import urlencode

from azure.eventgrid import EventGridEvent, SystemEventNames
from flask import Flask, Response, request, json, send_file, render_template, redirect, jsonify
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
from flask_cors import CORS


# Flask application setup
app = Flask(__name__)
CORS(app)

# Azure Services
ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")
ACS_PHONE_NUMBER = os.getenv("ACS_PHONE_NUMBER")
TARGET_PHONE_NUMBER = "+4915204446662"
COGNITIVE_SERVICES_ENDPOINT = os.getenv("COGNITIVE_SERVICES_ENDPOINT")
AZURE_OPENAI_SERVICE_KEY = os.getenv("AZURE_OPENAI_SERVICES_KEY")
CALLBACK_EVENTS_URI = "https://morehabitatforborkies-production.up.railway.app/api/callbacks"
SPEECH_TO_TEXT_VOICE = "en-US-NancyNeural"
OUTGOING_MESSAGE = "Hello! This is a notification from Wood Watcher." \
                   "We have detected potential environmental damage in your area of responsiblity." \
                   "We kindly ask you to call back this number to give us an update once you have investigated the situation. Thank you!"
call_automation_client = CallAutomationClient.from_connection_string(ACS_CONNECTION_STRING)
AZURE_OPENAI_DEPLOYMENT_MODEL = "gpt-3.5-turbo"
openai.api_key = AZURE_OPENAI_SERVICE_KEY

call_records = []
incidents = [
    {
        "incident_id": "a74b1de3-5d48-4376-93f6-8eb4185cf9c6",
        "timestamp": "2024-04-28T12:34:56",
        "location": "34.0522, -118.2437"
    },
    {
        "incident_id": "d8b39ccd-b9d7-4dbd-a4a1-6173e9019045",
        "timestamp": "2024-04-28T15:21:30",
        "location": "40.7128, -74.0060"
    }
]


def summarize_text(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a helpful office assistant looking over call transcripts. "
                                                "Take a look at the following transcript. "
                                                "Summarize it to the best of your ability."},
                  {"role": "user", "content": text}]
    )
    return response['choices'][0]['message']['content']


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


@app.route('/')
def hello_world():
    return "Hello World!"


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
                handle_recognize(
                    "Hello! Thanks for calling back! Please let us know what you have found out about the incident.",
                    caller_id, call_connection_id,
                    context="GetFreeFormText")

            elif event.type == "Microsoft.Communication.RecognizeCompleted":
                if event.data['recognitionType'] == "speech":
                    speech_text = event.data['speechResult']['speech'];
                    app.logger.info("Recognition completed, speech_text =%s", speech_text)
                    if speech_text is not None and len(speech_text) > 0:
                        summarized_text = summarize_text(speech_text)
                        static_response = "Thank you for your input. One of our representatives will be in touch if further context or action should be required. " \
                                          "If you are are not happy with the statement you gave or want to provide more context, just continue talking. Otherwise, feel free to hang up now."
                        handle_recognize(static_response, caller_id, call_connection_id, context="StaticResponse")
                        record_id = str(uuid.uuid4())
                        new_record = {
                            'record_id': record_id,
                            'timestamp': datetime.now(),
                            'caller_id': caller_id,
                            'speech_text': summarized_text
                        }
                        call_records.append(new_record)
                        app.logger.info("Call record added: %s", new_record)

            elif event.type == "Microsoft.Communication.RecognizeFailed":
                resultInformation = event.data['resultInformation']
                reasonCode = resultInformation['subCode']
                context = event.data['operationContext']
                global max_retry
                if reasonCode == 8510 and 0 < max_retry:
                    handle_recognize("Please repeat that.", caller_id, call_connection_id)
                    max_retry -= 1
                else:
                    handle_play(call_automation_client, "Have a wonderful day, goodbye!")

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


@app.route('/api/calls', methods=['GET'])
def get_calls():
    if not call_records:  # Check if the list is empty
        return jsonify({})  # Return an empty JSON object
    return jsonify(call_records)  # Return the list of call records as JSON


@app.route('/api/calls/<record_id>', methods=['GET'])
def get_call(record_id):
    record = next((item for item in call_records if item['record_id'] == record_id), None)
    return jsonify(record) if record else ('', 404)


@app.route('/api/calls', methods=['POST'])
def create_call():
    record_data = request.json
    record_id = str(uuid.uuid4())
    new_record = {
        'record_id': record_id,
        'timestamp': datetime.now(),
        'caller_id': record_data.get('caller_id', 'Unknown'),
        'speech_text': record_data.get('speech_text', '')
    }
    call_records.append(new_record)
    return jsonify(new_record), 201


@app.route('/api/calls/<record_id>', methods=['PUT'])
def update_call(record_id):
    record = next((item for item in call_records if item['record_id'] == record_id), None)
    if record:
        record_data = request.json
        record['caller_id'] = record_data.get('caller_id', record['caller_id'])
        record['speech_text'] = record_data.get('speech_text', record['speech_text'])
        return jsonify(record)
    else:
        return ('', 404)


@app.route('/api/calls/<record_id>', methods=['DELETE'])
def delete_call(record_id):
    global call_records
    call_records = [record for record in call_records if record['record_id'] != record_id]
    return Response(status=204)


@app.route('/api/incidents', methods=['POST'])
def create_incident():
    data = request.json
    incident_id = str(uuid.uuid4())
    new_incident = {
        'incident_id': incident_id,
        'timestamp': datetime.now(),
        'location': data.get('location', 'Unknown')
    }
    incidents.append(new_incident)
    return jsonify(new_incident), 201


# Endpoint to get all incidents
@app.route('/api/incidents', methods=['GET'])
def get_incidents():
    if not incidents:
        return jsonify({})
    return jsonify(incidents)


# Endpoint to get a single incident by ID
@app.route('/api/incidents/<incident_id>', methods=['GET'])
def get_incident(incident_id):
    incident = next((item for item in incidents if item['incident_id'] == incident_id), None)
    return jsonify(incident) if incident else ('', 404)


# Endpoint to update an incident
@app.route('/api/incidents/<incident_id>', methods=['PUT'])
def update_incident(incident_id):
    incident = next((item for item in incidents if item['incident_id'] == incident_id), None)
    if incident:
        data = request.json
        incident['location'] = data.get('location', incident['location'])
        return jsonify(incident)
    else:
        return ('', 404)


# Endpoint to delete an incident
@app.route('/api/incidents/<incident_id>', methods=['DELETE'])
def delete_incident(incident_id):
    global incidents
    incidents = [incident for incident in incidents if incident['incident_id'] != incident_id]
    return Response(status=204)


if __name__ == '__main__':
    app.logger.setLevel(INFO)
    app.run(host="0.0.0.0", debug=True, port=os.getenv("PORT", default=1234))
