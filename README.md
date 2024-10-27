# Rasa Chatbot for testbox.de

This repository contains a complete Rasa chatbot project, including Docker configurations, custom actions, and a frontend widget. The chatbot is built with Rasa, a conversational AI framework, and is set up to run in Docker containers using `docker-compose`.

## Project Structure

- **Dockerfile**: For the Rasa chatbot server.
- **action/Dockerfile**: For the custom Rasa action server.
- **action/requirements.txt**: Specifies dependencies for the action server.
- **docker-compose.yml**: Manages both Docker containers for the Rasa server and action server.
- **Chatbot-widget-main**: Contains the frontend code for the chatbot widget.

## Core Files

- **data/nlu.yml**: Contains training data for natural language understanding (NLU) to classify user intents and extract entities.
- **data/stories.yml**: Defines conversational training stories that teach the bot how to respond based on specific intents and contexts.
- **data/rules.yml**: Specifies rules that dictate conditional responses based on user inputs.
- **models**: Contains the machine learning model which is trained from the tarining data.
- **actions/actions.py**: Includes custom action code for handling complex responses or external API calls.
- **domain.yml**: Defines the intents, entities, slots, responses, and actions for the bot.
- **config.yml**: Configures the pipeline for NLU processing and the policy settings for managing conversation flow.
- **credentials.yml**: Contains credentials for connecting to external messaging platforms (e.g., Slack, Twilio).
- **endpoints.yml**: Defines endpoint configurations for the Rasa and action servers.
- **graph.html**: A visual representation of the conversation flow.
- **story_graph.dot**: A DOT file used to generate the `graph.html` representation of the bot’s conversation flow.

## Setup and Installation

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed on your machine.

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
2. **Run Docker Compose**: Start both the Rasa server and the action server
   ```bash
   docker-compose up --build
3. **Access the Chatbot**: After the containers are up, you can access the chatbot frontend from the **Chatbot-widget-main** folder by hosting it on a local or remote server. If you're running the Rasa server on a remote server, it is necessary to modify the `constants.js` and replace the localhost with the public IP address of the server.

Once you have you Rasa server up and running, you can test the bot by running the `index.html` file in the browser. More details on customizing the UI can be found inside `instructions.md` and `README.md` inside this folder.
