# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

import requests
import pandas as pd
import io
import yaml
import os
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted, SlotSet, AllSlotsReset, FollowupAction
# import json
# from rasa_sdk.types import DomainDict
# import random
# import re

class ActionDefaultFallback(Action):

    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_feedback_no")

        return [UserUtteranceReverted()]


class ActionTestCatalog(Action):
    def name(self) -> Text:
        return "action_test_catalog"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

#### Data Source #################################################################
##################################################################################

        # Option 1: Fetch data from the API
        url = 'https://api.testbox.de/api/test/list'
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            # Parse the response JSON
            df = pd.json_normalize(data)

            # Extract the user message
            # Use with slot
            test_slot = next(tracker.get_latest_entity_values("test"), None)
            test = tracker.get_slot("test") or test_slot

            if test is not None:
                test_name = self.test_catalog(df, test)

                print(test_name)

                if test_name is not None and not test_name.empty:
                    name = test_name['name'].tolist()
                    disorder = test_name['disorder'].tolist()  # Extract first row's 'disorder' value
                    slug = test_name['slug'].tolist()

                    # Ignore the [] braces
                    if isinstance(name, list):
                        name = ", ".join(name)
                        # Handle 'disorder' as a nested list
                    if isinstance(disorder, list) and isinstance(disorder[0], list):
                        disorder = [item for sublist in disorder for item in sublist]  # Flatten the nested list
                    if isinstance(disorder, list):
                        disorder = ", ".join(disorder)

                    response = f"Ich weiß Folgendes über {test}- \n" \
                               f"Name: <b>{name}</b>\n" \
                               f"Störung: {disorder}\n" \
                               f"Details: https://testbox.de/test/{slug}/details \n"
                else:
                    # when no matching age group found from api
                    response = f"Tut mir leid, ich weiß nichts über {test}.Sie können diese Seite für weitere Informationen besuchen https://testbox.de/test/category. Wenn Sie dort keine passende Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer Frage an tests@testbox.de"

                dispatcher.utter_message(text=response)
                # Trigger the feedback response (utter_feedback)
                return []

            else:
                # If the test name could not be extracted, trigger the utter_test_name response
                dispatcher.utter_message(response="utter_test_catalog")

        else:
            # If the request fails, send a message indicating the issue
            dispatcher.utter_message(text="Leider konnte ich Ihre Zielgruppe nicht identifizieren. Sie können diese Seite für weitere Informationen besuchen https://testbox.de/test/category. Wenn Sie dort keine passende Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer Frage an tests@testbox.de")
            return [FollowupAction(name="utter_feedback")]

        return [FollowupAction(name="action_reset_slot")]

    @staticmethod
    def test_catalog(df: pd.DataFrame, test: str) -> pd.DataFrame:
        # Convert the test string to lowercase for consistent case-insensitive comparison
        test = test.lower()
        print(test)

        # Search for the test name in both 'name' and 'variants' columns (case-insensitive)
        # Search in 'name' and 'time' columns, case insensitive
        name_match = df['name'].apply(lambda names: any(test in i.lower() for i in names))

        varinat_match = df['variants'].apply(lambda test_variants: any(test in i.lower() for i in test_variants))

        # Combine the matches
        matches = df[name_match | varinat_match]

        return matches

###########################################################################################################
#Option 2: Google Sheet, please uncomment the following when needed and comment out the above codes inside # tags
# Load the google sheet

    #     try:
    #         # Construct the URL for CSV export
    #         GOOGLE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/1DV9s6gLmgqPT0DioWgUpIVuuZeZQD_AXCpXc-G9TSLk/export?format=csv&gid=0"
    #
    #         # Fetch the CSV file from the Google Sheets URL
    #         response = requests.get(GOOGLE_SHEET_URL)
    #         response.raise_for_status()  # Raise an error for bad status codes
    #
    #         # Read the contents of the CSV file and store it in a pandas dataframe
    #         df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
    #
    #     except Exception as e:
    #         print(f"Error loading Google Sheet: {str(e)}")
    #
    #     # Extract the user message
    #     # Use with slot
    #     test_slot = next(tracker.get_latest_entity_values("test"), None)
    #     test = tracker.get_slot("test") or test_slot
    #
    #     if test is not None:
    #         test_name = self.test_catalog(df, test)
    #
    #         print(test_name)
    #
    #         if test_name is not None and not test_name.empty:
    #             name = test_name['name'].tolist()
    #             disorder = test_name['disorder'].tolist()  # Extract first row's 'disorder' value
    #             #slug = test_name['slug'].tolist()
    #
    #             # ignoring [ ] braces
    #             if isinstance(disorder, list):
    #                 disorder = ", ".join(disorder)
    #             if isinstance(name, list):
    #                 name = ", ".join(name)
    #
    #             response = f"Ich weiß Folgendes über {test}- \n" \
    #                        f"Name: <b>{name}</b>\n" \
    #                        f"Störung: {disorder}\n" \
    #                        #f"Details: https://testbox.de/test/{slug}/details \n"
    #
    #         else:
    #             response = f"Tut mir leid, ich weiß nichts über {test}.Sie können diese Seite für weitere Informationen besuchen https://testbox.de/test/category. Wenn Sie dort keine passende Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer Frage an tests@testbox.de"
    #
    #         dispatcher.utter_message(text=response)
    #         # Trigger the feedback response (utter_feedback)
    #         return []
    #
    #     else:
    #         # If the test name could not be extracted, trigger the utter_test_name response
    #         dispatcher.utter_message(response="utter_test_catalog")
    #
    #     return [FollowupAction(name="action_reset_slot")]
    #
    # @staticmethod
    # def test_catalog(df: pd.DataFrame, test: str) -> Dict[Text, Any]:
    #     # Convert the test string to lowercase for consistent case-insensitive comparison
    #     test = test.lower()
    #     print(test)
    #
    #     # Search for the test name in both 'name' and 'variants' columns (case-insensitive)
    #     # Search in 'name' and 'time' columns, case insensitive
    #     name_match = df['name'].fillna('').str.lower().str.contains(test)
    #     varinat_match = df['variants'].fillna('').str.lower().str.contains(test)
    #
    #     # Combine the matches
    #     matches = df[name_match | varinat_match]
    #
    #     return matches


##### Age ###############################################################################################################

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

            # Use with slot
            age_slot = next(tracker.get_latest_entity_values("age_group"), None)
            age_group = tracker.get_slot("age_group") or age_slot

            if age_group is not None:
                test_name = self.test_search_age(df, age_group)

                print(test_name)

                if test_name is not None and not test_name.empty:
                    name = test_name['name'].tolist()
                    disorder = test_name['disorder'].tolist() # Extract first row's 'disorder' value
                    slug = test_name['slug'].tolist()

                    # Construct the response with corresponding test names and disorders
                    response = f"Hier einige vorgeschlagene Tests:\n"

                    # Loop through paired names and disorders
                    for name, disorder, slug in zip(name, disorder, slug):
                        if isinstance(disorder, list):
                            disorder = ", ".join(disorder) # Join the list of disorders into a comma-separated string
                        # Construct the response with corresponding test names, disorders, and URLs
                        response += f"Test: <b>{name}</b>\n Störung: {disorder}\n Details: https://testbox.de/test/{slug}/details \n"
                else:
                    # when no matching age group found from api
                    response = f"Tut mir leid, ich finde keine test fur {age_group}. Sie können diese Seite für weitere Informationen besuchen https://testbox.de/test/category. Wenn Sie dort keine passende Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer Frage an tests@testbox.de"

                dispatcher.utter_message(text=response)
                # Trigger the feedback response (utter_feedback)
                return [FollowupAction(name="utter_feedback")]


        else:
            # If the request fails, send a message indicating the issue
            dispatcher.utter_message(text="Leider konnte ich Ihre Zielgruppe nicht identifizieren. Sie können diese Seite für weitere Informationen besuchen https://testbox.de/test/category. Wenn Sie dort keine passende Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer Frage an tests@testbox.de")
            return [FollowupAction(name="utter_feedback")]

        return [SlotSet("age_group", None)]


    @staticmethod
    def test_search_age(df: pd.DataFrame, age_group: str) -> pd.DataFrame:
        # Convert the test string to lowercase for consistent case-insensitive comparison
        age_group = age_group.lower()

        # Search for the test name in the 'age' column (case-insensitive)
        age_match = df['age'].apply(lambda ages: any(age_group in age.lower() for age in ages))

        # Filter the dataframe for matches
        matches = df[age_match]

        return matches

##### Disorder ###############################################################################################################

class ActionTestSearchDisorder(Action):
    def name(self) -> Text:
        return "action_test_search_disorder"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Load the google sheet
        try:
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
                slug = test_name['slug'].tolist()  # Extract first row's 'disorder' value

                # Construct the response with corresponding test names and disorders
                response = f"Hier einige vorgeschlagene Tests für {disorder}:\n"

                # Loop through paired names and disorders
                for name, slug in zip(name, slug):

                    response += f"Name: <b>{name}</b>\n" \
                                f"Details: https://testbox.de/test/{slug}/details \n"
            else:
                response = f"Tut mir leid, ich finde keine test fur {disorder}. Sie können diese Seite für weitere Informationen besuchen https://testbox.de/test/category. Wenn Sie dort keine passende Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer Frage an tests@testbox.de "

            dispatcher.utter_message(text=response)

            return [FollowupAction(name="utter_feedback")]

        else:
            # If the request fails, send a message indicating the issue
            dispatcher.utter_message(text="Tut mir leid, ich konnte Ihre Störung nicht identifizieren. Sie können diese Seite für weitere Informationen besuchen https://testbox.de/test/category. Wenn Sie dort keine passende Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer Frage an tests@testbox.de")
            return [FollowupAction(name="utter_feedback")]

        return [SlotSet('disorder', None)]


    @staticmethod
    def test_search_disorder(df: pd.DataFrame, disorder: str) -> Dict[Text, Any]:
        # Convert the test string to lowercase for consistent case-insensitive comparison
        disorder = disorder.lower()
        print(disorder)

        # Search for the test name in both 'name' and 'variants' columns (case-insensitive)
        # Search in 'name' and 'time' columns, case insensitive
        disorder_match = df['disorder_german_synonyms'].fillna('').str.lower().str.contains(disorder)
        # Combine the matches
        matches = df[disorder_match]

        return matches

###FAQ###****************************************************************************************************************
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

                elif matched_article is None:
                    # If no matched article is found, use the fallback utterance from the domain file
                    print(f"No match found, Answer from utter_question/{topic}") # Debug print
                    dispatcher.utter_message(response=f"utter_question/{topic}")

                else:
                    dispatcher.utter_message(text="Leider konnte ich keine Antwort auf Ihre Frage finden. Sie können diese Seite für weitere Informationen besuchen https://testbox.de/help. Wenn Sie dort keine passende Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer Frage an tests@testbox.de.")
            else:
                dispatcher.utter_message(text="Leider konnte ich zu diesem Zeitpunkt keine Daten von der API abrufen. Sie können diese Seite für weitere Informationen besuchen https://testbox.de/help. Wenn Sie dort keine passende Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer Frage an tests@testbox.de.")
        else:
            dispatcher.utter_message(text="Leider konnte ich die Intent Ihrer Anfrage nicht erkennen. Sie können diese Seite für weitere Informationen besuchen https://testbox.de/help. Wenn Sie dort keine passende Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer Frage an tests@testbox.de")

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


class ResetSlot(Action):
    def name(self):
        return "action_reset_slot"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("test", None), SlotSet("age_group", None), SlotSet("disorder", None)]