from bot.models.survey import Question, Survey
from services.validators import (
    validate_full_name, validate_block_number,
    validate_house_number, validate_household_count,
    validate_destination, validate_morning_time,
    validate_evening_time, validate_frequency, validate_phone_number
)
from config import DESTINATIONS, MORNING_SLOTS, FREQUENCY_OPTIONS

TRANSPORT_SURVEY = Survey(
    id="transport_registration",
    title="Transport Registration",
    questions=[
        Question(
            id="block_number",
            label="lbl_block",
            text="q_block",
            type="text",
            validator=validate_block_number
        ),
        Question(
            id="house_number",
            label="lbl_house",
            text="q_house",
            type="text",
            validator=validate_house_number,
            skippable=True
        ),
        Question(
            id="full_name",
            label="lbl_name",
            text="q_name",
            type="text",
            validator=validate_full_name
        ),
        Question(
            id="contact_phone",
            label="lbl_phone",
            text="q_phone",
            type="text",
            validator=validate_phone_number
        ),
        Question(
            id="destination",
            label="lbl_dest",
            text="q_dest",
            type="choice",
            options=DESTINATIONS,
            validator=validate_destination,
            keyboard_type="inline"
        ),
        Question(
            id="morning_departure_time",
            label="lbl_morning",
            text="q_morning",
            type="choice",
            options=MORNING_SLOTS,
            validator=validate_morning_time,
            keyboard_type="inline"
        ),
        Question(
            id="evening_pickup_time",
            label="lbl_evening",
            text="q_evening",
            type="text",
            validator=validate_evening_time
        ),
        Question(
            id="service_frequency",
            label="lbl_freq",
            text="q_freq",
            type="choice",
            options=FREQUENCY_OPTIONS,
            validator=validate_frequency,
            keyboard_type="inline"
        ),
    ]
)
