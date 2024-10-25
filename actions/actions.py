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

# Catching Mistakes, Failures and Human Handover Action
class ActionDefaultFallback(Action):

    def name(self) -> Text:
        return "action_default_fallback"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_feedback_no")

        return [UserUtteranceReverted()]

# Resetting all the slots
class ResetSlot(Action):
    def name(self):
        return "action_reset_slot"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("test", None), SlotSet("age_group", None), SlotSet("disorder", None)]


# Searching the tests by test name from API data, optional solution for google sheet is also provided in option 2
class ActionTestCatalog(Action):
    def name(self) -> Text:
        return "action_test_catalog"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Option 1: Fetch data from the API, uncomment this from here till end when option 2 is needed
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

                    response = f"Ich weiß Folgendes über {test}- \n"

                    for name, disorder, slug in zip(name, disorder, slug):
                        if isinstance(disorder, list):
                            disorder = ", ".join(disorder)  # Join the list of disorders into a comma-separated string
                        # Construct the response with corresponding test names, disorders, and URLs
                        response += f"Name: <b>{name}</b>\n Störung: {disorder}\n Details: https://testbox.de/test/{slug}/details \n"
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
    def normalize_test_name(test: str) -> str:
        """Normalize test name by removing special characters and extra spaces."""
        import re
        # Convert to lowercase and remove special characters
        normalized = re.sub(r'[^\w\s]', '', test.lower())
        # Remove extra spaces and trim
        normalized = ' '.join(normalized.split())
        return normalized

    @staticmethod
    def test_catalog(df: pd.DataFrame, test: str) -> pd.DataFrame:
        """
        Search for test name in the DataFrame using improved matching logic.
        """

        def find_match(value_list, search_term):
            # Handle both string and list inputs
            if isinstance(value_list, str):
                value_list = [value_list]

            # Normalize each value in the list
            normalized_values = [str(v).lower().strip() for v in value_list]
            search_term = search_term.lower().strip()

            # Try exact match first
            if search_term in normalized_values:
                return True

            # Then try partial match
            return any(search_term in value or value in search_term
                       for value in normalized_values)

        # Search in both name and variants columns
        name_match = df['name'].apply(lambda x: find_match(x, test))
        variant_match = df['variants'].apply(lambda x: find_match(x, test))

        # Combine matches and return results
        return df[name_match | variant_match]

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


# Searching the tests by Age group from API data
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


# Searching the tests by disorder name from Google Sheet
class ActionSearchDisorder(Action):
    def name(self) -> Text:
        return "action_test_search_disorder"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1DV9s6gLmgqPT0DioWgUpIVuuZeZQD_AXCpXc-G9TSLk/export?format=csv&gid=0"

        try:
            # Fetch and load the Google Sheet
            df = self.load_google_sheet(GOOGLE_SHEET_URL)

            # Get disorder from slot or entity
            disorder_slot = next(tracker.get_latest_entity_values("disorder"), None)
            disorder = tracker.get_slot("disorder") or disorder_slot

            if disorder is not None:
                # Clean and normalize the disorder input
                disorder = self.normalize_text(disorder)
                test_matches = self.search_disorder_tests(df, disorder)

                if not test_matches.empty:
                    response = self.format_test_results(disorder, test_matches)
                else:
                    response = self.get_no_results_message(disorder)

                dispatcher.utter_message(text=response)
                #return [FollowupAction(name="utter_feedback")]
            else:
                dispatcher.utter_message(
                    text="Tut mir leid, ich konnte Ihre Störung nicht identifizieren. "
                         "Sie können diese Seite für weitere Informationen besuchen "
                         "https://testbox.de/test/category. Wenn Sie dort keine passende "
                         "Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer "
                         "Frage an tests@testbox.de"
                )

        except Exception as e:
            print(f"Error in disorder search: {str(e)}")
            dispatcher.utter_message(
                text="Entschuldigung, es gab ein technisches Problem. "
                     "Bitte versuchen Sie es später noch einmal oder kontaktieren "
                     "Sie uns unter tests@testbox.de"
            )
        # Reset the slot and return the followup action
        return [SlotSet('disorder', None), FollowupAction(name="utter_feedback")]

    @staticmethod
    def load_google_sheet(url: str) -> pd.DataFrame:
        """Load and parse Google Sheet data."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return pd.read_csv(io.StringIO(response.content.decode('utf-8')))
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Google Sheet: {str(e)}")
        except pd.errors.EmptyDataError:
            raise Exception("The Google Sheet appears to be empty")
        except Exception as e:
            raise Exception(f"Error processing Google Sheet: {str(e)}")

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text by removing special characters and standardizing spaces."""
        import re

        # Convert to lowercase and remove special characters
        text = text.lower()
        # Replace German umlauts with their base characters
        umlaut_map = {
            'ä': 'a', 'ö': 'o', 'ü': 'u',
            'ß': 'ss', 'é': 'e', 'è': 'e',
            'á': 'a', 'à': 'a', 'ñ': 'n'
        }
        for umlaut, replacement in umlaut_map.items():
            text = text.replace(umlaut, replacement)

        # Remove special characters but keep spaces and hyphens
        text = re.sub(r'[^\w\s-]', '', text)
        # Normalize spaces and hyphens
        text = re.sub(r'[-\s]+', ' ', text)
        return text.strip()

    def search_disorder_tests(self, df: pd.DataFrame, disorder: str) -> pd.DataFrame:
        """
        Search for tests matching the disorder using improved matching logic.
        """

        def prepare_synonyms(synonyms_str):
            """Convert synonym string to list and normalize each term."""
            if pd.isna(synonyms_str) or not synonyms_str:
                return []
            return [self.normalize_text(syn.strip())
                    for syn in str(synonyms_str).split(',')]

        def find_match(synonyms_str, search_term):
            synonyms = prepare_synonyms(synonyms_str)

            # No synonyms found
            if not synonyms:
                return False

            # Try exact match first
            if search_term in synonyms:
                return True

            # Try partial matches
            search_parts = search_term.split()
            for synonym in synonyms:
                # Check if all parts of the search term are in the synonym
                if all(part in synonym for part in search_parts):
                    return True
                # Check if the synonym is completely contained in the search term
                if synonym in search_term:
                    return True

            return False

        # Normalize the disorder column and search for matches
        df['normalized_synonyms'] = df['disorder_german_synonyms'].apply(
            lambda x: prepare_synonyms(x)
        )

        # Search for matches
        matches = df[df['disorder_german_synonyms'].apply(
            lambda x: find_match(x, disorder)
        )]

        # Sort results by relevance (exact matches first)
        if not matches.empty:
            matches['relevance'] = matches['disorder_german_synonyms'].apply(
                lambda x: 1 if disorder in prepare_synonyms(x) else 0
            )
            matches = matches.sort_values('relevance', ascending=False)

        return matches[['name', 'slug']]  # Return only needed columns

    @staticmethod
    def format_test_results(disorder: str, matches: pd.DataFrame) -> str:
        """Format the matched tests into a response message."""
        response = f"Hier einige vorgeschlagene Tests für {disorder}:\n"

        for _, row in matches.iterrows():
            response += f"Name: <b>{row['name']}</b>\n" \
                        f"Details: https://testbox.de/test/{row['slug']}/details\n"

        return response.strip()

    @staticmethod
    def get_no_results_message(disorder: str) -> str:
        """Get the message to show when no results are found."""
        return (
            f"Tut mir leid, ich finde keine Tests für {disorder}. "
            f"Sie können diese Seite für weitere Informationen besuchen "
            f"https://testbox.de/test/category. Wenn Sie dort keine passende "
            f"Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer "
            f"Frage an tests@testbox.de"
        )



# Searching the answers for FAQ from Google sheet, optional solution to search from API data is also provided in option 2,
# comment out from Option 1 till option 2 and uncomment option 2 when needed
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
            # Extract topic (sub-intent) after 'faq/' (assuming intent format is 'faq/topic')
            topic = full_intent.split("/")[1] if "/" in full_intent else None
        else:
            topic = None

        if topic:
            # Step 2: Load intent examples from nlu.yml
            intent_examples = self.load_intent_examples_from_nlu(topic)

            # Step 3
            # Option 1: Load data from google sheet
            try:
                # Construct the URL for CSV export
                GOOGLE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/1rVFwy-R2noNlYDjVqo1fgBjnXdBwh2B0qXHFAdp412M/export?format=csv"

                # Fetch the CSV file from the Google Sheets URL
                response = requests.get(GOOGLE_SHEET_URL)
                response.raise_for_status()  # Raise an error for bad status codes

                # Read the contents of the CSV file and store it in a pandas dataframe
                df = pd.read_csv(io.StringIO(response.content.decode('utf-8')), sep=',', header=0)

                # Print the raw data to debug what was loaded
                print(df.head())  # Show first few rows of data
                print(f"Column names in DataFrame: {df.columns}")  # Print out the column names


                # Ensure 'title' and 'text' columns exist
                if 'title' in df.columns and 'text' in df.columns:
                    print("Successfully loaded data from Google Sheet.")
                else:
                    print("Error: 'title' or 'text' column not found in Google Sheet.")

                # Step 5: Match intent examples with the "title" field in API data
                matched_article = self.match_intent_example(intent_examples, df)

                if matched_article is not None:
                    # Send the response from the matched API data
                    response_text = matched_article.get('text')
                    dispatcher.utter_message(text=response_text)

                else:
                    # If no matched article is found, use the fallback utterance from the domain file
                    dispatcher.utter_message(text="utter_faq")

            except Exception as e:
                print(f"Error loading Google Sheet: {str(e)}")
                dispatcher.utter_message(
                text="Leider konnte ich zu diesem Zeitpunkt keine Daten von der API abrufen. Sie können diese Seite für weitere Informationen besuchen https://testbox.de/help. Wenn Sie dort keine passende Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer Frage an tests@testbox.de.")


        else:
            #cannot predict user input with faq intent
            dispatcher.utter_message(
                text="Leider konnte ich die Intent Ihrer Anfrage nicht erkennen. Sie können diese Seite für weitere Informationen besuchen https://testbox.de/help. Wenn Sie dort keine passende Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer Frage an tests@testbox.de")

        return []

            # Option 2: Fetch data from the API
        #     url = 'https://api.testbox.de/api/help/data'
        #     response = requests.get(url)
        #
        #     if response.status_code == 200:
        #         data = response.json()
        #         # Access the 'articles' list inside the 'data' dictionary
        #         articles_data = data.get('articles', [])
        #
        #         # Step 4: Normalize the API data using pandas
        #         df = pd.json_normalize(articles_data)
        #
        #         # Step 5: Match intent examples with the "title" field in API data
        #         matched_article = self.match_intent_example(intent_examples, df)
        #
        #         if matched_article is not None:
        #             # Send the response from the matched API data
        #             response_text = matched_article.get('text')
        #             dispatcher.utter_message(text=response_text)
        #
        #         elif matched_article is None:
        #             # If no matched article is found, use the fallback utterance from the domain file
        #             print(f"No match found, Answer from utter_question/{topic}") # Debug print
        #             dispatcher.utter_message(response=f"utter_question/{topic}")
        #
        #         else:
        #             dispatcher.utter_message(text="Leider konnte ich keine Antwort auf Ihre Frage finden. Sie können diese Seite für weitere Informationen besuchen https://testbox.de/help. Wenn Sie dort keine passende Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer Frage an tests@testbox.de.")
        #     else:
        #         dispatcher.utter_message(text="Leider konnte ich zu diesem Zeitpunkt keine Daten von der API abrufen. Sie können diese Seite für weitere Informationen besuchen https://testbox.de/help. Wenn Sie dort keine passende Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer Frage an tests@testbox.de.")
        # else:
        #     dispatcher.utter_message(text="Leider konnte ich die Intent Ihrer Anfrage nicht erkennen. Sie können diese Seite für weitere Informationen besuchen https://testbox.de/help. Wenn Sie dort keine passende Antwort finden, senden Sie uns bitte eine Anfrage mit Ihrer Frage an tests@testbox.de")
        #
        # return []

    def load_intent_examples_from_nlu(self, topic: str) -> List[str]:
        """
        Load examples for the given sub-intent (topic) from the nlu.yml file.
        """
        # Get the current working directory
        cwd = os.getcwd()

        # Construct the full path to the 'nlu.yml' file
        nlu_file_path = os.path.join(cwd, 'data/nlu.yml')
        with open(nlu_file_path, 'r', encoding='utf-8') as file:
            nlu_data = yaml.safe_load(file)

        # Search for the intent and its examples
        intent_examples = []
        for intent in nlu_data['nlu']:
            if intent['intent'] == f"faq/{topic}":  # Assuming intents are in this format
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
                print(f"Matched with title: {title}")
                return row.to_dict()  # Return the matched row as a dictionary

        print("No match found.")
        return None  # Return None if no match is found


