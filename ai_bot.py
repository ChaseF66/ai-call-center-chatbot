import random
import json
import os

# -------------------------------
# Helper functions
# -------------------------------
def looks_like_issue(user_input):
    lowered = user_input.lower()

    issue_words = [
        "leak", "leaking", "broken", "not working", "clog", "clogged", "sink",
        "toilet", "faucet", "shower", "pipe", "heat", "cooling", "power", "outlet",
        "water", "drain", "furnace", "hvac", "boiler", "ac", "air conditioner", "thermostat",
        "electrical", "breaker", "panel", "wiring"
    ]

    return any(word in lowered for word in issue_words)

def random_response(options):
    return random.choice(options)


def log_message(conversation_log, speaker, message):
    conversation_log.append(f"{speaker}: {message}")


def detect_mood(user_input, current_mood):
    lowered = user_input.lower()
    if any(word in lowered for word in ["angry", "mad", "frustrated", "ridiculous", "upset", "pissed", "furious", "damn",
                                        "horrible", "terrible", "awful", "worst", "unacceptable"]):
        return "angry"
    return current_mood


def detect_service_type(user_input):
    lowered = user_input.lower()

    if any(word in lowered for word in ["plumbing", "leak", "water", "drain", "pipe", "sink", "toilet", "faucet", "clog", "shower",]):
        return "Plumbing"
    elif any(word in lowered for word in ["furnace", "heat", "hvac", "boiler", "ac", "air conditioner", "thermostat"]):
        return "HVAC"
    elif any(word in lowered for word in ["electrical", "power", "outlet", "breaker", "panel", "wiring"]):
        return "Electrical"

    return None


def detect_day(user_input):
    lowered = user_input.lower().strip()

    days = [
        "monday", "tuesday", "wednesday",
        "thursday", "friday", "saturday", "sunday"
    ]

    for day in days:
        if day in lowered:
            return day.title()
        
    return None

def load_learned_responses():
    if os.path.exists("learned_responses.json"):
        with open("learned_responses.json", "r") as file:
            return json.load(file)
    return {}

def save_learned_responses(learned_responses):
    with open("learned_responses.json", "w") as file:
        json.dump(learned_responses, file, indent=4)

def log_unknown_question(user_input):
    with open("unknown_questions.txt", "a") as file:
        file.write(user_input.strip() + "\n")

def save_conversation(call_data):
    success_label = "BOOKED" if call_data["appointment_day"] else "NOT BOOKED"

    with open("call_log.txt", "a") as file:
        file.write("\n" + "=" * 60 + "\n")
        file.write(f"CALL #{call_data['call_id']} - {success_label}\n")
        file.write("=" * 60 + "\n")
        file.write(f"Customer Name: {call_data['customer_name']}\n")
        file.write(f"Service Type: {call_data['service_type']}\n")
        file.write(f"Issue: {call_data['issue_description']}\n")
        file.write(f"Appointment Day: {call_data['appointment_day']}\n")
        file.write(f"Appointment Window: {call_data['appointment_timeframe']}\n")
        file.write(f"Customer Mood: {call_data['customer_mood']}\n")
        file.write("-" * 60 + "\n")

        for line in call_data["conversation_log"]:
            file.write(line + "\n")

        file.write("=" * 60 + "\n")


def print_and_log(call_data, message):
    print("AI:", message)
    log_message(call_data["conversation_log"], "AI", message)


# -------------------------------
# Main chatbot logic
# -------------------------------
def handle_message(user_input, call_data, stats):
    call_data["customer_mood"] = detect_mood(user_input, call_data["customer_mood"])
    state = call_data["state"]

    if state == "start":
        response = "Hi, thanks for calling. What’s your name?"
        print_and_log(call_data, response)
        call_data["state"] = "get_name"

    elif state == "get_name":
        if looks_like_issue(user_input):
            response = "I can help with that. First, can I get your name?"
            print_and_log(call_data, response)
        else:
            call_data["customer_name"] = user_input.strip().title()
            response = f"Nice to meet you, {call_data['customer_name']}. What can I help you with today?"
            print_and_log(call_data, response)
            call_data["state"] = "identify_service"

    elif state == "identify_service":
        service_type = detect_service_type(user_input)

        if service_type:
            call_data["service_type"] = service_type
            call_data["context"]["service_type"] = service_type
            if "plumbing" in user_input or "leak" in user_input:
                call_data["context"]["service_type"] = "Plumbing"

            if service_type == "Plumbing":
                response = "Got it — this sounds like a plumbing issue. Can you tell me what’s going on?"
            elif service_type == "HVAC":
                response = "Got it — this sounds like a heating or cooling issue. Can you tell me what’s happening?"
            else:
                response = "Okay — this sounds like an electrical issue. Can you tell me more about it?"

            print_and_log(call_data, response)
            call_data["state"] = "diagnose_problem"
        else:
            response = "Can you tell me a little more about the kind of service you need?"
            print_and_log(call_data, response)

    elif state == "diagnose_problem":
        lowered = user_input.lower()

        if any(word in lowered for word in ["price", "cost", "how much", "quote"]):
            response = "I can help with that. Pricing depends on the exact issue, but we can schedule a visit so the technician can give you options and explain the next steps. Can you tell me what problem you're having with the system?"
            print_and_log(call_data, response)
            return call_data, stats
        
        call_data["issue_description"] = user_input.strip()
        call_data["context"]["issue"] = user_input.strip()

        if call_data["customer_mood"] == "angry":
            empathy_response = random_response([
                "I understand — that sounds really frustrating.",
                "I’m sorry you’re dealing with that.",
                "I can see why that would be upsetting."
            ])
            print_and_log(call_data, empathy_response)

        helpful_response = random_response([
            "We can definitely help with that.",
            "Thanks for explaining that — we can help.",
            "Got it. We should be able to take care of that."
        ])
        print_and_log(call_data, helpful_response)

        booking_response = "Would you like to get an appointment scheduled?"
        print_and_log(call_data, booking_response)
        call_data["state"] = "booking_offer"

    elif state == "booking_offer":
        lowered = user_input.lower()
        detected_day = detect_day(user_input)

        # handle price hesitation FIRST
        if any(word in lowered for word in ["price", "cost", "expensive"]):
            response = "I understand. We can schedule a visit so the technician can give you options and explain the next steps."
            print_and_log(call_data, response)
            return call_data, stats

        # yes + asap -> Today, Earliest
        if "yes" in lowered and any(word in lowered for word in ["asap", "soon", "today", "earliest"]):
            call_data["appointment_day"] = "Today"
            call_data["appointment_timeframe"] = "Earliest Available"

            if not call_data["appointment_booked"]:
                stats["booked_calls"] += 1
                call_data["appointment_booked"] = True

            response = (
                f"Perfect, {call_data['customer_name']}. I’ll mark this for today at the earliest available opening."
            )
            print_and_log(call_data, response)

            response = "If anything changes, let us know. Is there anything else I can help with?"
            print_and_log(call_data, response)

            call_data["state"] = "complete"
            return call_data, stats

        # then handle yes (without asap)
        if "yes" in lowered:
            response = "Perfect. What day would you like to schedule for?"
            print_and_log(call_data, response)
            call_data["state"] = "get_day"
            return call_data, stats

        # if customer skips ahead and gives a day directly
        if detected_day:
            call_data["appointment_day"] = detected_day
            response = f"Great, I see you mentioned {detected_day}. Would you prefer a morning or afternoon appointment?"
            print_and_log(call_data, response)
            call_data["state"] = "get_timeframe"
            return call_data, stats

        if "no" in lowered:
            response = random_response([
                "No problem. Is there anything you’re unsure about?",
                "That’s okay. What’s holding you back?",
                "Totally fine. Is it the timing, the price, or something else?"
            ])
            print_and_log(call_data, response)
            return call_data, stats

        response = "Just let me know if you’d like to get it scheduled."
        print_and_log(call_data, response)

    elif state == "get_day":
        detected_day = detect_day(user_input)
        lowered = user_input.lower()

        if detected_day:
            call_data["appointment_day"] = detected_day
        else:
            call_data["appointment_day"] = user_input.strip().title()

        if any(word in lowered for word in ["asap", "soon", "earliest"]):
            call_data["appointment_timeframe"] = "Earliest Available"
            if not call_data["appointment_booked"]:
                stats["booked_calls"] += 1
                call_data["appointment_booked"] = True

            response = (
                f"Perfect, {call_data['customer_name']}. I’ve got you scheduled for "
                f"{call_data['appointment_day']} at the earliest available time."
            )
            print_and_log(call_data, response)

            response = "If anything changes, let us know. Is there anything else I can help with?"
            print_and_log(call_data, response)

            call_data["state"] = "complete"
            return call_data, stats

        response = f"Got it — {call_data['appointment_day']}. Would you prefer a morning or afternoon appointment?"
        print_and_log(call_data, response)
        call_data["state"] = "get_timeframe"

    elif state == "get_timeframe":
        lowered = user_input.lower()

        if "morning" in lowered:
            call_data["appointment_timeframe"] = "Morning"
        elif "afternoon" in lowered:
            call_data["appointment_timeframe"] = "Afternoon"
        elif any(word in lowered for word in ["asap", "soon", "today", "earliest"]):
            call_data["appointment_timeframe"] = "Earliest Available"
        else:
            response = "Please choose either morning, afternoon, or earliest available."
            print_and_log(call_data, response)
            return call_data, stats

        if not call_data["appointment_booked"]:
            stats["booked_calls"] += 1
            call_data["appointment_booked"] = True

        response = (
            f"Perfect, {call_data['customer_name']}. I’ve got you scheduled for "
            f"{call_data['appointment_day']} in the {call_data['appointment_timeframe'].lower()}."
        )
        print_and_log(call_data, response)

        response = (
            f"To confirm: this is for a {call_data['service_type'].lower()} issue "
            f"({call_data['issue_description']}) on {call_data['appointment_day']} "
            f"in the {call_data['appointment_timeframe'].lower()}."
        )
        print_and_log(call_data, response)

        response = "If anything changes, let us know. Is there anything else I can help with?"
        print_and_log(call_data, response)

        call_data["state"] = "complete"

    elif state == "complete":
        lowered = user_input.lower()

        if "what is this for" in lowered or "what issue" in lowered:
            response = (
                f"This appointment is for your "
                f"{call_data['context']['service_type'].lower()} issue: "
                f"{call_data['context']['issue']}."
            )
            print_and_log(call_data, response)
            return call_data, stats

        if any(word in lowered for word in ["price", "cost", "pricing", "how much"]):
            response = "Pricing depends on the exact issue, but the technician will walk you through options before any work is done. Is there anything else you'd like the technician to take a look at?"

        elif any(word in lowered for word in ["also", "another", "additional", "water heater", "second issue", "furnace",
                                              "hvac", "boiler", "ac", "air conditioner", "thermostat", "electrical", "power", "outlet", "breaker", "panel", "wiring"]):
            response = "Absolutely — we can take a look at that during the same visit. I’ll make a note for the technician."
            call_data["issue_description"] += f" | Additional issue mentioned: {user_input}"

        elif any(word in lowered for word in ["what happens next", "next step"]):
            response = "The technician will arrive during the scheduled window, diagnose the issue, and explain your options before starting any work."

        elif any(word in lowered for word in ["how long", "duration"]):
            response = "Most diagnostic visits take about 30–60 minutes depending on the issue."

        elif any(word in lowered for word in ["what time", "timeframe", "window"]):
            response = (
                f"Your appointment is scheduled for {call_data['appointment_day']} "
                f"in the {call_data['appointment_timeframe'].lower()}."
            )

        elif any(word in lowered for word in ["what day", "date", "when"]):
            response = (
                f"Your appointment is scheduled for {call_data['appointment_day']} "
                f"in the {call_data['appointment_timeframe'].lower()}."
            )

        elif "name" in lowered:
            response = f"I have the appointment under the name {call_data['customer_name']}."

        elif any(word in lowered for word in ["service", "issue"]):
            response = (
                f"This is booked as a {call_data['service_type'].lower()} issue: "
                f"{call_data['issue_description']}."
            )

        else:
            learned_responses = call_data["learned_responses"]
            normalized_input = user_input.lower().strip().replace("?", "")

            if normalized_input in learned_responses:
                response = learned_responses[normalized_input]
            else:
                log_unknown_question(user_input)
                response = input("AI Trainer: I'm not sure how to respond here. What should I say? ")
                learned_responses[normalized_input] = response
                save_learned_responses(learned_responses)

        print_and_log(call_data, response)

    else:
        learned_responses = call_data["learned_responses"]
        normalized_input = user_input.lower().strip().replace("?", "")

        if normalized_input in learned_responses:
            print_and_log(call_data, learned_responses[normalized_input])
        else:
            log_unknown_question(user_input)
            new_response = input("AI Trainer: I'm not sure how to respond here. What should I say? ")
            learned_responses[normalized_input] = new_response
            save_learned_responses(learned_responses)
            print_and_log(call_data, new_response)

    return call_data, stats


# -------------------------------
# App loop
# -------------------------------

stats = {
    "total_calls": 1,
    "booked_calls": 0
}

call_id = 1
def create_new_call(call_id):
    return {
        "call_id": call_id,
        "state": "start",
        "customer_mood": "neutral",
        "customer_name": "",
        "appointment_day": "",
        "appointment_timeframe": "",
        "service_type": "",
        "issue_description": "",
        "conversation_log": [],
        "appointment_booked": False,
        "learned_responses": load_learned_responses(),
        "context": {
            "service_type": None,
            "issue": None
        }
    }

call_data = create_new_call(call_id)

while True:
    user_input = input("\nCustomer: ")
    log_message(call_data["conversation_log"], "Customer", user_input)

    if user_input.lower() == "exit":
        save_conversation(call_data)

        print("\nAI: Appreciate you reaching out — have a great day!")
        print(f"\nTotal Calls: {stats['total_calls']}")
        print(f"Booked Appointments: {stats['booked_calls']}")

        if stats["total_calls"] > 0:
            conversion_rate = (stats["booked_calls"] / stats["total_calls"]) * 100
            print(f"Conversion Rate: {conversion_rate:.2f}%")

        print("\nConversation Log:")
        for line in call_data["conversation_log"]:
            print(line)

        break

    if user_input.lower() == "restart":
        save_conversation(call_data)
        call_id += 1
        stats["total_calls"] += 1
        call_data = create_new_call(call_id)
        print("\n--- Restarting Conversation ---")
        continue

    print("\nAI: Thinking...\n")
    call_data, stats = handle_message(user_input, call_data, stats)
