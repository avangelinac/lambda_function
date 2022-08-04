### Required Libraries ###
from datetime import datetime
from imp import init_builtin
from dateutil.relativedelta import relativedelta

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")


def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot
        }

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {
            "contentType": "PlainText",
            "content": message_content
        }
    }


def get_initial_recommendation(risk_level):
    """
    Define a response message for the risk_level entry.
    """
    if risk_level.lower() == "none":
        initial_recommendation="100% bonds (AGG), 0% equities (SPY)"
    if risk_level.lower() == "low":
        initial_recommendation="60% bonds (AGG), 40% equities (SPY)"
    if risk_level.lower() == "medium":
        initial_recommendation="40% bonds (AGG), 60% equities (SPY)"
    if risk_level.lower() == "high":
        initial_recommendation="20% bonds (AGG), 80% equities (SPY)"
    print(risk_level)
    return initial_recommendation


def validate_data(age, investment_amount, intent_request):
    """
    Validates the data provided by the user.
    * The `age` should be greater than zero and less than 65.
    * The `investment_amount` should be equal to or greater than 5000.
    """    
    if age is not None:
        age = parse_int(age)
        if age < 0 or age > 64:
            return build_validation_result(
                False,
                "age",
                "The maximum age to contract this service is 64, can you provide an age between 0 and 64 please?"
            )

    if investment_amount is not None:
        investment_amount = parse_int(investment_amount)
        if investment_amount < 5000:
            return build_validation_result(
                False,
                "investmentAmount",
                "The minimum investment amount is $5,000 USD, could you please provide a greater amount?"
            )
        
    return build_validation_result(True, None, None)


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Delegate",
            "slots": slots
        },
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response


### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    # Gets slots' values
    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]

    # Gets the invocation source, for Lex dialogs "DialogCodeHook" is expected.
    source = intent_request["invocationSource"]
    
    # This code performs basic validation on the supplied input slots.
    # Gets all the slots
    if source == "DialogCodeHook":
        # Validates user's input using the validate_data function
        slots = get_slots(intent_request)
        
        if slots == 'age':
            print("line 149 slots = 'age'")
        # Use the elicitSlot dialog action to re-prompt
        # for the first violation detected.
        # Perform basic validation on the supplied input slots.
        # Validates user's input using the validate_data function
        validation_result = validate_data(age, investment_amount, intent_request)
        
        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None 
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"]
            )

        # Fetch current session attibutes
        output_session_attributes = intent_request["sessionAttributes"]

        return delegate(output_session_attributes, get_slots(intent_request))

    # Get the initial investment recommendation
    if risk_level:
        initial_recommendation = get_initial_recommendation(risk_level)
    else:
        initial_recommendation = "Unfortunately we need a risk level to make a recommendation"

    # Return a message with the initial recommendation based on the risk level.
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """Thank you {} for your information. 
            Based on the '{}' risk level you provided, the recommendation is an investment portfolio with: {}""".format(first_name, risk_level, initial_recommendation),
        },
    )


### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "recommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    return dispatch(event)