# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

import requests
import json
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted, SlotSet, AllSlotsReset, FollowupAction
from rasa_sdk.types import DomainDict
import pandas as pd
import io
import random
import yaml
import os
import re

class ActionDefaultFallback(Action):

    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_feedback_no")

        return [UserUtteranceReverted()]

class ActionHyperlink(Action):

    def name(self) -> Text:
        return "action_hyperlink"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        link1 = "https://testbox.de/browsers"
        dispatcher.utter_template("utter_question/supported_devices", tracker, link=link1)

        return []


class GoogleSheet(Action):
    """Rasa action to parse user text and pull a corresponding answer
    from Google Sheets based on the intent and entities.
    If there is no answer in the Google Sheet, it will use the ChatGPT API."""

    def name(self) -> Text:
        return "google_sheet"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Set the environment variable for testing purposes
        os.environ["SHEET_URL"] = "1aHXOFLyUd6J3elNlCbT1xgKaHN9LAJwCkHjuFKKOzqY"

        # Get the latest user text, intent, and entities
        user_text = tracker.latest_message.get('text')
        intent = tracker.latest_message.get('intent').get('name')
        entities = tracker.latest_message.get('entities')

        # Fetch the answer from Google Sheets
        answer = self.get_answers_from_sheets(intent, entities, user_text)

        # Dispatch the response
        dispatcher.utter_message(text=answer)

        return []

    def get_answers_from_sheets(self, intent, entities, user_text):
        try:
            # Connect to Google Sheets
            sheet_url = os.getenv("SHEET_URL")  # Ensure this environment variable is set correctly
            if not sheet_url:
                return "Sorry, I couldn't find the Google Sheet URL."

            GOOGLE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{sheet_url}/export?format=csv&gid=0"
            response = requests.get(GOOGLE_SHEET_URL)
            response.raise_for_status()  # Raise an error for bad status codes

            # Read the contents of the URL as a CSV file and store it in a dataframe
            proxy_df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))

            if entities:
                entity_value = entities[0].get('value')
                filtered_df = proxy_df[(proxy_df['Intent'] == intent) & (proxy_df['Entity'] == entity_value)]

                if filtered_df.empty:
                    answer = self.get_answer_from_chatgpt(user_text)
                else:
                    answers = filtered_df['Answer'].tolist()
                    answer = random.choice(answers)
            else:
                answer = self.get_answer_from_chatgpt(user_text)

            return answer
        except Exception as e:
            return f"An error occurred: {str(e)}"

    def get_answer_from_chatgpt(self, user_text):
        # Placeholder for the ChatGPT API call
        # This function should call the OpenAI API and return a response based on the user_text
        return "This is a fallback response from ChatGPT API."


class ActionTestCatalog(Action):
    def name(self) -> Text:
        return "action_test_catalog"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Load the Excel file
        file_path = 'F:\\MSc TUK WS19-20\\Thesis\\Chatbot\\test_catalog_sample.xlsx'
        df = pd.read_excel(file_path)

        # Extract the user message
        # Use with slot
        test_slot = next(tracker.get_latest_entity_values("test"), None)
        test = tracker.get_slot("test") or test_slot

        # user_intent = tracker.latest_message['intent'].get('name')

        if test is not None:
            test_name = self.test_catalog(df, test)

            print(test_name)

            if test_name is not None and not test_name.empty:
                full_name = test_name.iloc[0]['full_name']  # Extract first row's 'full_name' value
                disorder = test_name.iloc[0]['disorder']  # Extract first row's 'disorder' value

                response = f"Here is what I know about {test}: \n" \
                          f"Full Name: {full_name}\n" \
                          f"Disorder: {disorder}"
            else:
                response = f"Tut mir leid, ich weiß nichts über {test}"

            dispatcher.utter_message(text=response)
            # Trigger the feedback response (utter_feedback)
            return [FollowupAction(name="utter_feedback")]

        else:
            # If the test name could not be extracted, trigger the utter_test_name response
            dispatcher.utter_message(response="utter_test_catalog")

        return []


    @staticmethod
    def test_catalog(df: pd.DataFrame, test: str) -> Dict[Text, Any]:
        # Convert the test string to lowercase for consistent case-insensitive comparison
        test = test.lower()
        print(test)

        # Search for the test name in both 'name' and 'variants' columns (case-insensitive)
        # Search in 'name' and 'time' columns, case insensitive
        name_match = df['name'].fillna('').str.lower().str.contains(test)
        varinat_match = df['variants'].fillna('').str.lower().str.contains(test)

        # Combine the matches
        matches = df[name_match | varinat_match]

        return matches

class ActionTestSearchAge(Action):
    def name(self) -> Text:
        return "action_test_search_age"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Load the Excel file
        # Fetch data from the API
        url = 'https://api.testbox.de/api/test/list'
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            # Parse the response JSON
            df = pd.json_normalize(data)

            # file_path = 'F:\\MSc TUK WS19-20\\Thesis\\Chatbot\\test_catalog_sample.xlsx'
            # df = pd.read_excel(file_path)

            # Use with slot
            age_slot = next(tracker.get_latest_entity_values("age_group"), None)
            age_group = tracker.get_slot("age_group") or age_slot

            if age_group is not None:
                test_name = self.test_search_age(df, age_group)

                print(test_name)

                if test_name is not None and not test_name.empty:
                    name = test_name['name'].tolist()
                    disorder = test_name['disorder'].tolist()  # Extract first row's 'disorder' value

                    # Construct the response with corresponding test names and disorders
                    response = f"Here are some suggested tests for {age_group}:\n"

                    # Loop through paired names and disorders
                    for name, disorder in zip(name, disorder):
                        response += f"Test Name: {name}, Disorder: {disorder}\n"
                else:
                    response = f"Tut mir leid, ich finde keine test fur {age_group}"

                dispatcher.utter_message(text=response)
                # Trigger the feedback response (utter_feedback)
                return [FollowupAction(name="utter_feedback")]

        else:
            # If the request fails, send a message indicating the issue
            dispatcher.utter_message(text="Sorry, I couldn't retrieve data at this time.")
            return []

        return []


    @staticmethod
    def test_search_age(df: pd.DataFrame, age_group: str) -> pd.DataFrame:
        # Convert the test string to lowercase for consistent case-insensitive comparison
        age_group = age_group.lower()

        # Search for the test name in the 'age' column (case-insensitive)
        age_match = df['age'].apply(lambda ages: any(age_group in age.lower() for age in ages))

        # Filter the dataframe for matches
        matches = df[age_match]

        return matches

    # def test_search_age(df: pd.DataFrame, age_group: str) -> Dict[Text, Any]:
    #     # Convert the test string to lowercase for consistent case-insensitive comparison
    #     age_group = age_group.lower()
    #     print(age_group)
    #
    #     # Search for the test name in both 'name' and 'variants' columns (case-insensitive)
    #     # Search in 'name' and 'time' columns, case insensitive
    #     age_match = df['age'].fillna('').str.lower().str.contains(age_group)
    #     # Combine the matches
    #     matches = df[age_match]

        # return matches

#
class ActionTestSearchDisorder(Action):
    def name(self) -> Text:
        return "action_test_search_disorder"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Load the google sheet
        try:
            # Get the Google Sheet ID from the environment variable
            # os.environ["SHEET_URL"] = "1DV9s6gLmgqPT0DioWgUpIVuuZeZQD_AXCpXc-G9TSLk"
            # sheet_url = os.getenv("SHEET_URL")
            # if not sheet_url:
            #     raise ValueError("Sorry, I couldn't find the Google Sheet URL.")

            # Construct the URL for CSV export
            GOOGLE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/1DV9s6gLmgqPT0DioWgUpIVuuZeZQD_AXCpXc-G9TSLk/export?format=csv&gid=0"

            # Fetch the CSV file from the Google Sheets URL
            response = requests.get(GOOGLE_SHEET_URL)
            response.raise_for_status()  # Raise an error for bad status codes

            # Read the contents of the CSV file and store it in a pandas dataframe
            df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))

        except Exception as e:
            print(f"Error loading Google Sheet: {str(e)}")

        # Use with slot
        disorder_slot = next(tracker.get_latest_entity_values("disorder"), None)
        disorder = tracker.get_slot("disorder") or disorder_slot

        if disorder is not None:
            test_name = self.test_search_disorder(df, disorder)

            print(test_name)

            if test_name is not None and not test_name.empty:
                name = test_name['name'].tolist()
                variants = test_name['variants'].tolist()  # Extract first row's 'disorder' value

                # Construct the response with corresponding test names and disorders
                response = f"Here are some suggested tests for {disorder}:\n"

                # Loop through paired names and disorders
                for name, variants in zip(name, variants):
                    if not variants:
                        variants = "Keine"
                    response += f"Test Name: {name}, variants: {variants}\n"
            else:
                response = f"Tut mir leid, ich finde keine test fur {disorder}"

            dispatcher.utter_message(text=response)
            # Trigger the feedback response (utter_feedback)
            return [FollowupAction(name="utter_feedback")]

        return []


    @staticmethod
    def test_search_disorder(df: pd.DataFrame, disorder: str) -> Dict[Text, Any]:
        # Convert the test string to lowercase for consistent case-insensitive comparison
        disorder = disorder.lower()
        print(disorder)

        # Search for the test name in both 'name' and 'variants' columns (case-insensitive)
        # Search in 'name' and 'time' columns, case insensitive
        disorder_match = df['disorder'].fillna('').str.lower().str.contains(disorder)
        # Combine the matches
        matches = df[disorder_match]

        return matches

class ActionQuestionsHelp(Action):
    def name(self) -> Text:
        return "action_faq"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Step 1: Get the full sub-intent using response selector
        full_intent_data = tracker.latest_message.get("response_selector", {}).get('default',{}).get('response',{})
        full_intent = full_intent_data.get("intent_response_key",None)  # Extract sub-intent

        print(f"Full intent: {full_intent}")  # Debugging print
        if full_intent:
            # Extract topic (sub-intent) after 'question/' (assuming intent format is 'question/topic')
            topic = full_intent.split("/")[1] if "/" in full_intent else None
        else:
            topic = None

        if topic:
            # Step 2: Load intent examples from nlu.yml
            intent_examples = self.load_intent_examples_from_nlu(topic)

            # Step 3: Fetch data from the API
            url = 'https://api.testbox.de/api/help/data'
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                # Access the 'articles' list inside the 'data' dictionary
                articles_data = data.get('articles', [])

                # Step 4: Normalize the API data using pandas
                df = pd.json_normalize(articles_data)

                # Step 5: Match intent examples with the "title" field in API data
                matched_article = self.match_intent_example(intent_examples, df)

                if matched_article is not None:
                    # Send the response from the matched API data
                    response_text = matched_article.get('text')
                    dispatcher.utter_message(text=response_text)
                else:
                    dispatcher.utter_message(text="Sorry, I couldn't find a response matching your query.")
            else:
                dispatcher.utter_message(text="Sorry, I couldn't retrieve data from the API at this time.")
        else:
            dispatcher.utter_message(text="Sorry, I couldn't identify your query intent.")

        return []

    def load_intent_examples_from_nlu(self, topic: str) -> List[str]:
        """
        Load examples for the given sub-intent (topic) from the nlu.yml file.
        """
        # Get the current working directory
        cwd = os.getcwd()

        # Construct the full path to the 'nlu.yml' file
        nlu_file_path = os.path.join(cwd, 'data\\nlu.yml')
        with open(nlu_file_path, 'r', encoding='utf-8') as file:
            nlu_data = yaml.safe_load(file)

        # Search for the intent and its examples
        intent_examples = []
        for intent in nlu_data['nlu']:
            if intent['intent'] == f"question/{topic}":  # Assuming intents are in this format
                examples = intent.get('examples', "").strip().split("\n")
                intent_examples = [ex.strip('- ') for ex in examples]  # Clean up examples
                break
        print(f"Intent examples: {intent_examples}")  # Debugging print
        return intent_examples

    @staticmethod
    def match_intent_example(intent_examples: List[str], df: pd.DataFrame) -> Dict[Text, Any]:
        """
        Match the intent examples with the 'title' field in the articles DataFrame.
        If a match is found, return the matched row as a dictionary; otherwise, return None.
        """
        # Normalize both intent examples and title for case-insensitive matching
        intent_examples = [example.lower() for example in intent_examples]

        # Iterate over the DataFrame to find matching titles
        for _, row in df.iterrows():
            title = row['title'].lower()

            # Check if any intent example matches the title
            if any(example in title for example in intent_examples):
                return row.to_dict()  # Return the matched row as a dictionary

        return None  # Return None if no match is found


# class TestSearchForm(FormValidationAction):
#     def name(self) -> Text:
#         return "action_form_test_search"
#
#     @staticmethod
#     def required_slots(tracker: Tracker) -> List[Text]:
#         return ["age_group", "disorder"]


# # to reset all the slots
# class ActionSlotReset(Action):
#     def name(self):
#         return 'action_slot_reset'
#
#     def run(self, dispatcher, tracker, domain):
#         return [AllSlotsReset()]

# reset the test slot
class ResetSlot(Action):
    def name(self):
        return "action_reset_slot"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("test", None)]