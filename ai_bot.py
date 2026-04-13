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

    plumbing_words = [
        "plumbing", "leak", "water", "drain", "pipe",
        "sink", "toilet", "faucet", "clog", "shower"
    ]

    hvac_words = [
        "furnace", "heat", "hvac", "boiler",
        "ac", "air conditioner", "thermostat"
    ]

    electrical_words = [
        "electrical", "power", "outlet",
        "breaker", "panel", "wiring"
    ]

    plumbing_score = sum(word in lowered for word in plumbing_words)
    hvac_score = sum(word in lowered for word in hvac_words)
    electrical_score = sum(word in lowered for word in electrical_words)

    scores = {
        "Plumbing": plumbing_score,
        "HVAC": hvac_score,
        "Electrical": electrical_score
    }

    best_match = max(scores, key=lambda k: scores[k])
    confidence = scores[best_match]

    if confidence == 0:
        return None, 0

    return best_match, confidence


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

def detect_intents(user_input):
    lowered = user_input.lower()

    intent_keywords = {
        "pricing": [
            "price", "cost", "quote", "estimate", "pricing", "expensive", "how much"
        ],
        "urgency": [
            "asap", "soon", "today", "earliest", "earliest available", "immediately", "right away", "urgent"
        ],
        "yes": [
            "yes", "sure", "yeah", "yup", "ok", "okay"
        ],
        "no": [
            "no", "nope", "nah", "negative", "not right now"
        ],
        "appointment_question": [
            "what time", "time frame", "timeframe", "window", "what day", "date", "when", "what is the day", "which day", "date", "when is it", "when is the appointment"
        ],
        "service_question": [
            "what is this for", "what issue is this", "what service is this", "what did i book"
        ],
        "next_step": [
            "what happens next", "next step", "what do i do", "after this"
        ],
        "duration_question": [
            "how long", "duration", "how much time"
        ],
        "name_question": [
            "what name is it under", "whose name", "under what name", "who is it under", "what name do you have", "who is this for", "who is the appointment for", "what customer name"
        ],
        "additional_issue": [
            "also", "another", "additional", "second issue",
            "water heater", "furnace", "hvac", "boiler", "ac",
            "air conditioner", "thermostat", "electrical", "power",
            "outlet", "breaker", "panel", "wiring"
        ],
        "morning": [
            "morning"
        ],
        "afternoon": [
            "afternoon",
        ]
    }

    detected_intents = set()

    for intent, keywords in intent_keywords.items():
        for keyword in keywords:
            if keyword in lowered:
                detected_intents.add(intent)
                break

    return detected_intents


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
INTENT_PRIORITY = [
    "urgency",
    "yes",
    "pricing",
    "additional_issue",
    "appointment_question",
    "service_question",
    "next_step",
    "duration_question",
    "name_question"
]

def get_primary_intent(intents):
    for intent in INTENT_PRIORITY:
        if intent in intents:
            return intent
    return None

def handle_message(user_input, call_data, stats):
    call_data["customer_mood"] = detect_mood(user_input, call_data["customer_mood"])
    state = call_data["state"]
    intents = detect_intents(user_input)
    detected_day = detect_day(user_input)
    lowered = user_input.lower()

    if state == "start":
        response = "Hi, thanks for calling. What’s your name?"
        print_and_log(call_data, response)
        call_data["state"] = "get_name"
        return call_data, stats

    elif state == "get_name":
        if looks_like_issue(user_input):
            response = "I can help with that. First, can I get your name?"
            print_and_log(call_data, response)
        else:
            call_data["customer_name"] = user_input.strip().title()
            response = f"Nice to meet you, {call_data['customer_name']}. What can I help you with today?"
            print_and_log(call_data, response)
            call_data["state"] = "identify_service"
        return call_data, stats

    elif state == "identify_service":
        service_type, confidence = detect_service_type(user_input)

        if service_type:
            call_data["service_type"] = service_type
            call_data["context"]["service_type"] = service_type
            call_data["issue_description"] = user_input.strip()
            call_data["context"]["issue"] = user_input.strip()

            if confidence == 1:
                response = f"I believe this may be a {service_type.lower()} issue — can you tell me a little more about what’s going on?"
            else:
                response = f"This sounds like a {service_type.lower()} issue. Can you tell me more about the problem?"

            print_and_log(call_data, response)
            call_data["state"] = "diagnose_problem"
        else:
            response = "Can you tell me a little more about the kind of service you need?"
            print_and_log(call_data, response)
        return call_data, stats

    elif state == "diagnose_problem":
        primary_intent = get_primary_intent(intents)

        # acknowledge multiple intents
        if len(intents) > 1:
            readable_intents = [intent.replace("_", " ") for intent in intents]

            multi_response = (
                "I can help with multiple things: " +
                ", ".join(readable_intents) +
                ". Let's go step by step."
            )
            print_and_log(call_data, multi_response)

        if primary_intent == "pricing":
            response = "I can help with that. Pricing depends on the exact issue, but we can schedule a visit so the technician can give you options and explain the next steps. Can you tell me what problem you're having with the system?"
            print_and_log(call_data, response)
            return call_data, stats

        if looks_like_issue(user_input):
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
        return call_data, stats

    elif state == "booking_offer":
        lowered = user_input.lower()
        detected_day = detect_day(user_input)
        intents = detect_intents(user_input)

        # handle price hesitation FIRST
        if "pricing" in intents:
            response = "I understand. We can schedule a visit so the technician can give you options and explain the next steps."
            print_and_log(call_data, response)

            if "yes" in intents or detected_day or "urgency" in intents:
                follow_up = "If you'd like, we can still get you scheduled now. What day works best for you?"
                print_and_log(call_data, follow_up)

            return call_data, stats

        # yes + asap -> Today, Earliest
        if "yes" in intents and "urgency" in intents:
            call_data["appointment_day"] = "Today"
            call_data["appointment_timeframe"] = "Earliest Available"

            if not call_data["appointment_booked"]:
                stats["booked_calls"] += 1
                call_data["appointment_booked"] = True

            response = f"Perfect, {call_data['customer_name']}. I’ll mark this for today at the earliest available opening."
            print_and_log(call_data, response)

            response = f"If anything changes, let us know. Is there anything else I can help with?"
            print_and_log(call_data, response)

            call_data["state"] = "complete"
            return call_data, stats

        # yes + specific day
        if "yes" in intents and detected_day:
            call_data["appointment_day"] = detected_day
            response = f"Great, I can get you in on {detected_day}. Would you prefer a morning or afternoon appointment?"
            print_and_log(call_data, response)
            call_data["state"] = "get_timeframe"
            return call_data, stats

        if "no" in intents:
            response = random_response([
                "No problem. Is there anything you’re unsure about?",
                "That’s okay. What’s holding you back?",
                "Totally fine. Is it the timing, the price, or something else?"
            ])
            print_and_log(call_data, response)
            return call_data, stats

        # if customer gives a day directly
        if detected_day:
            call_data["appointment_day"] = detected_day
            response = f"Great, I see you mentioned {detected_day}. Would you prefer a morning or afternoon appointment?"
            print_and_log(call_data, response)
            call_data["state"] = "get_timeframe"
            return call_data, stats

        # default prompt to get a day
        if "yes" in intents:
            response = "Perfect. What day works best for you?"
            print_and_log(call_data, response)
            call_data["state"] = "get_day"
            return call_data, stats

        response = "Just let me know if you'd like to get it scheduled."
        print_and_log(call_data, response)
        return call_data, stats

    elif state == "get_day":
        intents = detect_intents(user_input)
        detected_day = detect_day(user_input)
        lowered = user_input.lower()

        if "urgency" in intents or "earliest available" in lowered:
            call_data["appointment_day"] = "Today"
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

        if detected_day:
            call_data["appointment_day"] = detected_day
            response = f"Got it — {call_data['appointment_day']}. Would you prefer a morning or afternoon appointment?"
            print_and_log(call_data, response)
            call_data["state"] = "get_timeframe"
            return call_data, stats

        response = "What day works best for you? You can say something like Monday, Tuesday, or earliest available."
        print_and_log(call_data, response)
        return call_data, stats


    elif state == "get_timeframe":
        intents = detect_intents(user_input)
        lowered = user_input.lower()

        if "morning" in intents:
            call_data["appointment_timeframe"] = "Morning"
        elif "afternoon" in intents:
            call_data["appointment_timeframe"] = "Afternoon"
        elif "urgency" in intents or any(word in lowered for word in ["asap", "soon", "earliest"]):
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
        return call_data, stats

    elif state == "complete":
        intents = detect_intents(user_input)
        response_parts = []

        if "service_question" in intents:
            response_parts.append(
                f"This appointment is for your "
                f"{call_data['context']['service_type'].lower()} issue: "
                f"{call_data['context']['issue']}."
            )

        if "appointment_question" in intents:
            response_parts.append(
                f"Your appointment is scheduled for {call_data['appointment_day']} "
                f"in the {call_data['appointment_timeframe'].lower()}."
            )

        if "name_question" in intents:
            response_parts.append(
                f"I have the appointment under the name {call_data['customer_name']}."
            )

        if "pricing" in intents:
            response_parts.append(
                "Pricing depends on the exact issue, but the technician will walk you "
                "through options before any work is done."
            )

        if "next_step" in intents:
            response_parts.append(
                "The technician will arrive during the scheduled window, diagnose the issue, and explain your options before starting any work."
            )

        if "duration_question" in intents:
            response_parts.append(
                "Most diagnostic visits take about 30–60 minutes depending on the issue."
            )

        if "additional_issue" in intents or looks_like_issue(user_input):
            response_parts.append(
                "Absolutely — we can take a look at that during the same visit. I’ll make a note for the technician."
            )
            call_data["issue_description"] += f" | Additional issue mentioned: {user_input}"

        if response_parts:
            response = " ".join(response_parts)
            print_and_log(call_data, response)
            return call_data, stats


        learned_responses = call_data["learned_responses"]
        normalized_input = user_input.lower().strip().replace("?", "")

        if normalized_input in learned_responses:
            response = learned_responses[normalized_input]
        else:
            log_unknown_question(user_input)
            response = "AI Trainer: I'm not sure how to respond to that. What should I say?"
            learned_responses[normalized_input] = response
            save_learned_responses(learned_responses)

        print_and_log(call_data, response)
        return call_data, stats

        

    # fallback - learn new responses
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
