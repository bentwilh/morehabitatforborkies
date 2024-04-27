import os
from logging import INFO

from flask import Flask, Response
from azure.communication.callautomation import (
    CallAutomationClient, PhoneNumberIdentifier, TextSource)

# Flask application setup
app = Flask(__name__)

# Your ACS resource connection string, source and target phone numbers
ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")
ACS_PHONE_NUMBER = os.getenv("ACS_PHONE_NUMBER")
TARGET_PHONE_NUMBER = "+4915204446662"

# Callback URI to handle events.
CALLBACK_EVENTS_URI = "https://morehabitatforborkies-production.up.railway.app/api/callbacks"

# Text-to-speech voice and initial announcement text
SPEECH_TO_TEXT_VOICE = "en-US-NancyNeural"
INITIAL_ANNOUNCEMENT = "Hello, this is notification from wood watchers. How much wood would a wood watcher watch? Goodbye."

# Create the call automation client
call_automation_client = CallAutomationClient.from_connection_string(ACS_CONNECTION_STRING)


@app.route('/')
def hello_world():
    return "Hello World!"


@app.route('/outboundCall', methods=['GET'])
def outbound_call():
    source = PhoneNumberIdentifier(ACS_PHONE_NUMBER)
    target = PhoneNumberIdentifier(TARGET_PHONE_NUMBER)

    # Start an outbound call
    call_connection = call_automation_client.create_call(
        source_caller_id_number=source,
        target_participant=target,
        callback_uri=CALLBACK_EVENTS_URI
    )

    # Retrieve the call connection client
    call_connection_client = call_automation_client.get_call_connection(call_connection.call_connection_id)

    # Play announcement
    text_source = TextSource(text=INITIAL_ANNOUNCEMENT, voice_name=SPEECH_TO_TEXT_VOICE)
    call_connection_client.play_media_to_all(text_source)

    # Hang up after the announcement
    call_connection_client.hang_up(is_for_everyone=True)

    return Response("Call initiated and message sent.", status=200)


@app.route('/api/callbacks', methods=['POST'])
def callback_events_handler():
        return Response(status=200)


if __name__ == '__main__':
    app.logger.setLevel(INFO)
    app.run(host="0.0.0.0", debug=True, port=os.getenv("PORT", default=1234))

