import streamlit as st
import json
import os
import threading
import hashlib
import uuid
import re

from plyer import notification


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AlertLoop AI",
    page_icon="🔔",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# ============================================================
# FILE STORAGE
# ============================================================

USER_FILE = "users.json"


def initialize_database():

    if not os.path.exists(USER_FILE):

        with open(
            USER_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                {},
                file,
                indent=4
            )


initialize_database()


def load_users():

    try:

        with open(
            USER_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (
        json.JSONDecodeError,
        FileNotFoundError
    ):

        return {}


def save_users(users):

    with open(
        USER_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            users,
            file,
            indent=4
        )


# ============================================================
# PASSWORD SECURITY
# ============================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# ============================================================
# EMAIL / PHONE VALIDATION
# ============================================================

def is_valid_email(value):

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return re.match(
        pattern,
        value
    ) is not None


def is_valid_phone(value):

    phone = value.replace(
        " ",
        ""
    ).replace(
        "-",
        ""
    )

    if phone.startswith("+"):

        phone = phone[1:]

    return phone.isdigit() and 10 <= len(phone) <= 15


def normalize_identifier(value):

    value = value.strip()

    if "@" in value:

        return value.lower()

    return (
        value
        .replace(" ", "")
        .replace("-", "")
    )


# ============================================================
# NOTIFICATION SYSTEM
# ============================================================

notification_events = {}


def send_notification(
    title,
    message
):

    try:

        notification.notify(
            title=title,
            message=message,
            timeout=4
        )

    except Exception:
        pass


def notify_loop(
    notification_id,
    title,
    message
):

    event = notification_events.get(
        notification_id
    )

    if event is None:
        return

    while not event.is_set():

        send_notification(
            title,
            message
        )

        event.wait(5)


def start_notification(
    notification_id,
    category,
    message
):

    event = threading.Event()

    notification_events[
        notification_id
    ] = event

    thread = threading.Thread(
        target=notify_loop,
        args=(
            notification_id,
            category,
            message
        ),
        daemon=True
    )

    thread.start()


def stop_notification(
    notification_id
):

    event = notification_events.get(
        notification_id
    )

    if event:

        event.set()

    notification_events.pop(
        notification_id,
        None
    )


# ============================================================
# NOTIFICATION CATEGORIZATION
# ============================================================

def categorize(text):

    text = text.lower().strip()

    if "exam" in text:

        return "Exam", "High"

    elif "assignment" in text:

        return "Assignment", "Medium"

    elif "placement" in text:

        return "Placement", "High"

    elif "event" in text:

        return "Event", "Low"

    elif "holiday" in text:

        return "Holiday", "Low"

    else:

        return "General", "Low"


# ============================================================
# CREATE NOTICE
# ============================================================

def create_notice(text):

    category, priority = categorize(
        text
    )

    return {

        "id":
            str(uuid.uuid4()),

        "text":
            text,

        "category":
            category,

        "priority":
            priority
    }


# ============================================================
# SESSION STATE
# ============================================================

# No splash screen.
# Application starts directly on Login.

if "page" not in st.session_state:

    st.session_state.page = "login"


if "user" not in st.session_state:

    st.session_state.user = None


if "identifier" not in st.session_state:

    st.session_state.identifier = None


if "notices" not in st.session_state:

    st.session_state.notices = []


# ============================================================
# SAVE CURRENT NOTICES
# ============================================================

def save_current_notices():

    if not st.session_state.identifier:

        return

    users = load_users()

    identifier = (
        st.session_state.identifier
    )

    if identifier in users:

        users[identifier]["notices"] = (
            st.session_state.notices
        )

        save_users(users)


# ============================================================
# LOGIN PAGE
# ============================================================

if st.session_state.page == "login":

    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    st.title("🔔 AlertLoop AI")

    st.caption(
        "Smart notifications that keep you on track."
    )

    st.divider()

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    st.header("Welcome Back 👋")

    st.write(
        "Login to continue to your notification dashboard."
    )

    st.write("")

    identifier = st.text_input(
        "Email or Phone Number",
        placeholder="Enter your email or phone number"
    )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password"
    )

    st.write("")

    if st.button(
        "🔐 Login",
        use_container_width=True,
        type="primary"
    ):

        identifier = normalize_identifier(
            identifier
        )

        if not identifier or not password:

            st.warning(
                "Please enter your email/phone number and password."
            )

        else:

            users = load_users()

            hashed_password = hash_password(
                password
            )

            if (
                identifier in users
                and users[identifier]["password"]
                == hashed_password
            ):

                st.session_state.user = (
                    users[identifier]["name"]
                )

                st.session_state.identifier = (
                    identifier
                )

                st.session_state.notices = (
                    users[identifier].get(
                        "notices",
                        []
                    )
                )

                st.session_state.page = "home"

                st.rerun()

            else:

                st.error(
                    "Invalid email/phone number or password ❌"
                )

    st.write("")

    # --------------------------------------------------------
    # FORGOT PASSWORD
    # --------------------------------------------------------

    if st.button(
        "🔑 Forgot Password?",
        use_container_width=True
    ):

        st.session_state.page = (
            "forgot_password"
        )

        st.rerun()

    st.write("")

    st.divider()

    st.caption(
        "Don't have an account?"
    )

    if st.button(
        "📝 Create New Account",
        use_container_width=True
    ):

        st.session_state.page = (
            "register"
        )

        st.rerun()


# ============================================================
# REGISTER PAGE
# ============================================================

elif st.session_state.page == "register":

    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    st.title("🔔 AlertLoop AI")

    st.caption(
        "Create your account and start managing reminders."
    )

    st.divider()

    # --------------------------------------------------------
    # REGISTRATION
    # --------------------------------------------------------

    st.header("Create Account")

    st.write(
        "Create an account using your email or phone number."
    )

    st.write("")

    name = st.text_input(
        "Full Name",
        placeholder="Enter your name"
    )

    identifier = st.text_input(
        "Email or Phone Number",
        placeholder="Enter your email or phone number"
    )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Minimum 6 characters"
    )

    confirm_password = st.text_input(
        "Confirm Password",
        type="password",
        placeholder="Re-enter your password"
    )

    st.write("")

    if st.button(
        "📝 Create Account",
        use_container_width=True,
        type="primary"
    ):

        identifier = normalize_identifier(
            identifier
        )

        if not name.strip():

            st.warning(
                "Please enter your name."
            )

        elif not identifier:

            st.warning(
                "Please enter your email or phone number."
            )

        elif not (
            is_valid_email(identifier)
            or is_valid_phone(identifier)
        ):

            st.warning(
                "Please enter a valid email address or phone number."
            )

        elif len(password) < 6:

            st.warning(
                "Password must contain at least 6 characters."
            )

        elif password != confirm_password:

            st.error(
                "Passwords do not match."
            )

        else:

            users = load_users()

            if identifier in users:

                st.error(
                    "This email/phone number is already registered."
                )

            else:

                users[identifier] = {

                    "name":
                        name.strip(),

                    "password":
                        hash_password(
                            password
                        ),

                    "notices":
                        []

                }

                save_users(users)

                st.success(
                    "Account created successfully! ✅"
                )

                st.session_state.page = (
                    "login"
                )

                st.rerun()

    st.write("")

    st.divider()

    if st.button(
        "← Back to Login",
        use_container_width=True
    ):

        st.session_state.page = (
            "login"
        )

        st.rerun()


# ============================================================
# FORGOT PASSWORD PAGE
# ============================================================

elif st.session_state.page == "forgot_password":

    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    st.title("🔔 AlertLoop AI")

    st.caption(
        "Securely recover your account."
    )

    st.divider()

    # --------------------------------------------------------
    # RESET PASSWORD
    # --------------------------------------------------------

    st.header("Reset Password 🔑")

    st.write(
        "Enter the email or phone number linked to your account."
    )

    st.write("")

    identifier = st.text_input(
        "Email or Phone Number",
        placeholder="Enter your email or phone number"
    )

    new_password = st.text_input(
        "New Password",
        type="password",
        placeholder="Enter your new password"
    )

    confirm_password = st.text_input(
        "Confirm New Password",
        type="password",
        placeholder="Re-enter your new password"
    )

    st.write("")

    if st.button(
        "🔄 Reset Password",
        use_container_width=True,
        type="primary"
    ):

        identifier = normalize_identifier(
            identifier
        )

        users = load_users()

        if not identifier:

            st.warning(
                "Please enter your email or phone number."
            )

        elif identifier not in users:

            st.error(
                "No account found with this email/phone number."
            )

        elif len(new_password) < 6:

            st.warning(
                "Password must contain at least 6 characters."
            )

        elif new_password != confirm_password:

            st.error(
                "Passwords do not match."
            )

        else:

            users[identifier]["password"] = (
                hash_password(
                    new_password
                )
            )

            save_users(users)

            st.success(
                "Password reset successfully! ✅"
            )

            st.session_state.page = (
                "login"
            )

            st.rerun()

    st.write("")

    st.divider()

    if st.button(
        "← Back to Login",
        use_container_width=True
    ):

        st.session_state.page = (
            "login"
        )

        st.rerun()


# ============================================================
# HOME PAGE
# ============================================================

elif st.session_state.page == "home":

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.title("🔔 AlertLoop AI")

    st.caption(
        "Your smart notification dashboard."
    )

    st.divider()

    st.header(
        f"Welcome, {st.session_state.user} 👋"
    )

    st.write(
        "Stay informed. Stay organized."
    )

    st.divider()

    # --------------------------------------------------------
    # QUICK STATS
    # --------------------------------------------------------

    total_notifications = len(
        st.session_state.notices
    )

    high_priority = sum(
        1
        for notice
        in st.session_state.notices
        if notice["priority"] == "High"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Active",
            total_notifications
        )

    with col2:

        st.metric(
            "High Priority",
            high_priority
        )

    st.divider()

    # ========================================================
    # ADD REMINDER
    # ========================================================

    st.header("➕ Add Reminder")

    st.write(
        "Add an important reminder and AlertLoop AI will categorize it."
    )

    reminder = st.text_input(
        "Reminder",
        placeholder="Example: Exam tomorrow"
    )

    if st.button(
        "🔔 Add Reminder",
        use_container_width=True,
        type="primary"
    ):

        if not reminder.strip():

            st.warning(
                "Please enter a reminder."
            )

        else:

            reminder = reminder.strip()

            already_exists = any(

                notice["text"].lower()
                == reminder.lower()

                for notice
                in st.session_state.notices

            )

            if already_exists:

                st.warning(
                    "This reminder already exists."
                )

            else:

                notice = create_notice(
                    reminder
                )

                st.session_state.notices.append(
                    notice
                )

                save_current_notices()

                start_notification(
                    notice["id"],
                    notice["category"],
                    notice["text"]
                )

                st.success(
                    f"{notice['category']} reminder added! 🔔"
                )

                st.rerun()


    # ========================================================
    # ACTIVE NOTIFICATIONS
    # ========================================================

    st.divider()

    st.header("🔔 Active Notifications")

    if not st.session_state.notices:

        st.info(
            "No active notifications."
        )

    else:

        for notice in st.session_state.notices:

            if notice["priority"] == "High":

                icon = "🔴"

            elif notice["priority"] == "Medium":

                icon = "🟡"

            else:

                icon = "🟢"

            with st.container(
                border=True
            ):

                st.subheader(
                    f"{icon} {notice['category']}"
                )

                st.write(
                    notice["text"]
                )

                st.caption(
                    f"Priority: {notice['priority']}"
                )

                if st.button(
                    "✅ Mark as Completed",
                    key=f"complete_{notice['id']}",
                    use_container_width=True
                ):

                    stop_notification(
                        notice["id"]
                    )

                    st.session_state.notices = [

                        item

                        for item
                        in st.session_state.notices

                        if item["id"]
                        != notice["id"]

                    ]

                    save_current_notices()

                    st.rerun()


    # ========================================================
    # ACCOUNT
    # ========================================================

    st.divider()

    st.header("Account")

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "➕ Add Account",
            use_container_width=True
        ):

            st.session_state.page = (
                "register"
            )

            st.rerun()

    with col2:

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):

            for notice in (
                st.session_state.notices
            ):

                stop_notification(
                    notice["id"]
                )

            st.session_state.user = None

            st.session_state.identifier = None

            st.session_state.notices = []

            st.session_state.page = (
                "login"
            )

            st.rerun()