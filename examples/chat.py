# -*- coding: utf-8 -*-

"""A chat/shoutbox using Sijax."""

import os
import hmac
from hashlib import sha1

from flask import Flask, g, render_template, session, abort, request
from werkzeug.security import safe_str_cmp
import flask_sijax

app = Flask(__name__)
app.secret_key = os.urandom(128)

@app.template_global('csrf_token')
def csrf_token():
    """
    Generate a token string from bytes arrays. The token in the session is user
    specific.
    """
    if "_csrf_token" not in session:
        session["_csrf_token"] = os.urandom(128)
    return hmac.new(app.secret_key, session["_csrf_token"],
            digestmod=sha1).hexdigest()

@app.before_request
def check_csrf_token():
    """Checks that token is correct, aborting if not"""
    if request.method in ("GET",): # not exhaustive list
        return
    token = request.form.get("csrf_token")
    if token is None:
        app.logger.warning("Expected CSRF Token: not present")
        abort(400)
    if not safe_str_cmp(token, csrf_token()):
        app.logger.warning("CSRF Token incorrect")
        abort(400)

# The path where you want the extension to create the needed javascript files
# DON'T put any of your files in this directory, because they'll be deleted!
app.config["SIJAX_STATIC_PATH"] = os.path.join('.', os.path.dirname(__file__), 'static/js/sijax/')

# You need to point Sijax to the json2.js library if you want to support
# browsers that don't support JSON natively (like IE <= 7)
app.config["SIJAX_JSON_URI"] = '/static/js/sijax/json2.js'

flask_sijax.Sijax(app)

class SijaxHandler(object):
    """A container class for all Sijax handlers.

    Grouping all Sijax handler functions in a class
    (or a Python module) allows them all to be registered with
    a single line of code.
    """

    @staticmethod
    def save_message(obj_response, message):

        message = message.strip()
        if message == '':
            return obj_response.alert("Empty messages are not allowed!")

        # Save message to database or whatever..

        import time, hashlib
        time_txt = time.strftime("%H:%M:%S", time.gmtime(time.time()))
        message_id = 'message_%s' % hashlib.sha256(time_txt.encode("utf-8")).hexdigest()

        message = """
        <div id="%s" style="opacity: 0;">
            [<strong>%s</strong>] %s
        </div>
        """ % (message_id, time_txt, message)

        # Add message to the end of the container
        obj_response.html_append('#messages', message)

        # Clear the textbox and give it focus in case it has lost it
        obj_response.attr('#message', 'value', '')
        obj_response.script("$('#message').focus();")

        # Scroll down the messages area
        obj_response.script("$('#messages').attr('scrollTop', $('#messages').attr('scrollHeight'));")

        # Make the new message appear in 400ms
        obj_response.script("$('#%s').animate({opacity: 1}, 400);" % message_id)


    @staticmethod
    def clear_messages(obj_response):

        # Delete all messages from the database

        # Clear the messages container
        obj_response.html('#messages', '')

        # Clear the textbox
        obj_response.attr('#message', 'value', '')

        # Ensure the texbox has focus
        obj_response.script("$('#message').focus();")


@flask_sijax.route(app, "/")
def index():
    if g.sijax.is_sijax_request:
        # The request looks like a valid Sijax request
        # Let's register the handlers and tell Sijax to process it
        g.sijax.register_object(SijaxHandler)
        return g.sijax.process_request()

    return render_template('chat.html')

if __name__ == '__main__':
    app.run(debug=True, port=8080)

