import streamlit as st
from io import BytesIO
import re


# --- Page Config ---
st.set_page_config(page_title="ACP/Lifeline Assistant", layout="wide")

# --- Title Visible on the Page ---
st.title("ACP/Lifeline Assistant")


# --- Style ---
st.markdown("""
    <style>
    body {
        background-color: white !important;
        color: black;
    }
    .chat-bubble {
        padding: 12px 16px;
        border-radius: 16px;
        margin: 8px 0;
        max-width: 75%;
        word-wrap: break-word;
        display: inline-block;
        font-size: 16px;
    }
    .bot-bubble {
        background-color: #f1f1f1;
        color: black;
        text-align: left;
        float: left;
        clear: both;
    }
    .user-bubble {
        background-color: #d1e7dd;
        color: black;
        text-align: left;
        float: right;
        clear: both;
    }
    .clearfix::after {
        content: "";
        display: table;
        clear: both;
    }
    .message-input {
        border-radius: 24px;
        padding: 10px;
        width: 100%;
        font-size: 16px;
    }
    .send-btn {
        background: #2c7be5;
        color: white;
        border: none;
        padding: 10px 16px;
        border-radius: 50%;
        cursor: pointer;
        font-size: 18px;
        margin-left: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.title("Welcome to our ACP/Lifeline application assistant. For further help, please chat with our virtual assistant")
# Future integrations can go here

# --- Initialize Session State ---
if 'step' not in st.session_state:
    st.session_state.update({
        'step': 'start',
        'user_type': None,
        'id_type': None,
        'user_id': None,
        'photo_uploaded': False,
        'photo_name': None,
        'photo_data': None,
        'application_type': None,
        'confirmed': False,
        'duplicate': False,
        'chat_history': [],
        'progress': 0
    })

# --- Existing Records for Duplicate Check ---
existing_records = [
    {"id": "123-45-6789", "photo": "passport.png"},
    {"id": "555-66-7777", "photo": "duplicate.png"},
    {"id": "999-88-7777", "photo": "jane.png"},
]

# --- Chat Bubble ---
def chat_bubble(message, sender='bot', save_to_history=True):
    avatar = "🤖" if sender == 'bot' else "🧑"
    bubble_class = 'bot-bubble' if sender == 'bot' else 'user-bubble'
    st.markdown(
        f"""
        <div class="chat-bubble {bubble_class} clearfix">
            <strong>{avatar} {sender.capitalize()}:</strong> {message}
        </div>
        """,
        unsafe_allow_html=True
    )
    if save_to_history:
        st.session_state.chat_history.append({'text': message, 'sender': sender})

# --- Replay History ---
for msg in st.session_state.chat_history:
    chat_bubble(msg['text'], sender=msg['sender'], save_to_history=False)

# --- Progress Bar ---
st.progress(st.session_state.progress)

# --- Validate ID ---
def validate_id(user_input):
    if st.session_state.id_type == 'ssn':
        return bool(re.match(r"^\d{3}-\d{2}-\d{4}$", user_input))
    elif st.session_state.id_type == 'tribal':
        return user_input.isdigit() and len(user_input) >= 5
    return False

# --- Bot Reply Logic ---
def bot_reply(user_input):
    step = st.session_state.step

    if step == 'awaiting_id':
        if validate_id(user_input):
            st.session_state.user_id = user_input
            st.session_state.step = 'awaiting_photo'
            st.session_state.progress = 60
            chat_bubble("✅ ID confirmed. Now please upload your photo for verification.", sender='bot')
        else:
            chat_bubble("⚠️ Please enter a valid SSN (e.g., 123-45-6789) or Tribal ID (at least 5 digits).", sender='bot')

    elif step == 'awaiting_confirmation':
        if 'yes' in user_input:
            st.session_state.confirmed = True
            st.session_state.step = 'done'
            chat_bubble("✅ Details sent to NLAD.", sender='bot')
            chat_bubble("📅 Most applications are processed in 1–2 business days.", sender='bot')
        elif 'no' in user_input:
            chat_bubble("Okay! Let me know when you're ready to proceed.", sender='bot')
        else:
            chat_bubble("Please respond with 'yes' or 'no'.", sender='bot')

    elif step == 'awaiting_provider_switch':
        st.session_state.step = 'done'
        chat_bubble("Thanks! We'll help you switch your provider soon.", sender='bot')

    elif step == 'done':
        chat_bubble("🙏 Thank you for using the assistant. Have a great day!", sender='bot')

# --- Handle Photo Upload ---
def handle_photo_upload(uploaded_photo):
    if uploaded_photo:
        st.session_state.photo_uploaded = True
        st.session_state.photo_name = uploaded_photo.name
        st.session_state.photo_data = uploaded_photo.getvalue()
        chat_bubble(f"📸 Photo '{uploaded_photo.name}' uploaded successfully!", sender='bot')
        st.image(BytesIO(uploaded_photo.getvalue()), caption="Uploaded Photo", use_column_width=True)

        for record in existing_records:
            if record['id'] == st.session_state.user_id and record['photo'].lower() == uploaded_photo.name.lower():
                st.session_state.duplicate = True
                st.session_state.step = 'awaiting_provider_switch'
                chat_bubble("⚠️ Duplicate detected: You are already registered.", sender='bot')
                chat_bubble("Would you like to switch providers instead? (yes/no)", sender='bot')
                return

        st.session_state.step = 'awaiting_confirmation'
        chat_bubble("✅ No duplicate found. Do you want to submit your details to NLAD? (yes/no)", sender='bot')



# --- Welcome & User Type ---
if st.session_state.step == 'start':
    if 'welcome_shown' not in st.session_state:
        st.session_state.welcome_shown = True
        chat_bubble("Hi there! 👋 I’m here to help you apply for ACP or Lifeline.", sender='bot')
        chat_bubble("Are you a new user or an existing user?", sender='bot')
    col1, col2 = st.columns(2)
    if col1.button("🆕 New"):
        st.session_state.user_type = 'new'
        st.session_state.step = 'ask_id_type'
        chat_bubble("New user selected.", sender='user')
        chat_bubble("What type of ID will you use?", sender='bot')
    if col2.button("👤 Existing"):
        st.session_state.user_type = 'existing'
        st.session_state.step = 'ask_id_type'
        chat_bubble("Existing user selected.", sender='user')
        chat_bubble("What type of ID will you use?", sender='bot')

# --- ID Type Selection ---
if st.session_state.step == 'ask_id_type':
    col1, col2 = st.columns(2)
    if col1.button("SSN"):
        st.session_state.id_type = 'ssn'
        st.session_state.step = 'awaiting_id'
        chat_bubble("SSN selected.", sender='user')
        chat_bubble("You selected SSN. Please enter your SSN (e.g., 123-45-6789).", sender='bot')
    if col2.button("Tribal ID"):
        st.session_state.id_type = 'tribal'
        st.session_state.step = 'awaiting_id'
        chat_bubble("Tribal ID selected.", sender='user')
        chat_bubble("You selected Tribal ID. Please enter your ID (at least 5 digits).", sender='bot')

# --- ID Entry ---
if st.session_state.step == 'awaiting_id':
    with st.form("id_form", clear_on_submit=True):
        user_input = st.text_input("Enter your ID:", key="id_input")
        submitted = st.form_submit_button("➤")
        if submitted and user_input:
            chat_bubble(user_input, sender='user')
            bot_reply(user_input)
            st.rerun()

# --- Photo Upload ---
if st.session_state.step == 'awaiting_photo':
    uploaded_file = st.file_uploader("Upload your photo", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        chat_bubble(f"[Uploaded: {uploaded_file.name}]", sender='user')
        handle_photo_upload(uploaded_file)
        st.rerun()

# --- Final Confirmation or Provider Switch ---
if st.session_state.step in ['awaiting_confirmation', 'awaiting_provider_switch']:
    with st.form("confirm_form", clear_on_submit=True):
        user_input = st.text_input("Your response:", key="confirm_input")
        submitted = st.form_submit_button("➤")
        if submitted and user_input:
            chat_bubble(user_input, sender='user')
            bot_reply(user_input.lower())
            st.rerun()

# --- Reset ---
if st.button("🔄 Reset Chat"):
    st.session_state.clear()
    st.rerun()
