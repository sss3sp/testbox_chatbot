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

2. **Adding Model**: Please download & add the trained 
[model](https://drive.google.com/file/d/1hmeU330TpbOvpz01qJZb8ZnJsqShgDMM/view?usp=drive_link) inside **models** directory.

4. **Run Docker Compose**: Start both the Rasa server and the action server
   ```bash
   docker-compose up --build

5. **Access the Chatbot**: After the containers are up, you can access the chatbot frontend from the **Chatbot-widget-main** folder by hosting it on a local or remote server. If you're running the Rasa server on a remote server, it is necessary to modify the [constants.js](Chatbot-Widget-main/static/js/constants.js) and replace the localhost with the public IP address of the server.

6. **Train the Chatbot**: You can train the rasa chatbot after updating the nlu, domain or stories file by using the following commands.
   ```bash
   rasa train
   rasa train --force #In case if the 1st one doesn't train the model with your updates

7. **Test & rebuild in docker**: After traing the new model you can test it directly from command line using the following commnads.
   ```bash
   rasa run #you can also specify the the latest model and rest api if you wan to to run it from the UI like following
   rasa run -m models --enable-api --cors "*" --debug
   rasa run –model models/20190506-100418.tar.gz #to run a specific model
   rasa run actions #for the action server or
   rasa run actions --cors "*" --debug

You can also find more useful commands here https://rasa.com/docs/rasa/command-line-interface/
After testing you need to rebuild the docker file again.

8. **Human Hand off**: You can follow this projects to implement human handoff configuration. 
https://github.com/rasahq/helpdesk-assistant?tab=readme-ov-file#handoff
https://github.com/RasaHQ/chatroom?tab=readme-ov-file#setting-up-handoff-capability
https://rasa.com/docs/rasa/next/connectors/your-own-website

9. **Rasa community**: You can also ask for any help or any issues directly in rasa community. 
https://forum.rasa.com/

10. **POC Chatbot**: You will get the the code for the RAG based chatbot inside POC folder. You need to download mistral LLM and huggingfacembedding model and also need to change the training data path ebfore running it.


Once you have you Rasa server up and running, you can test the bot by running the [index.html](Chatbot-Widget-main/index.html) file in the browser. More details on customizing the UI can be found in [README.md](Chatbot-Widget-main/static/js/constants.js) inside this folder.

A short [video](https://screenrec.com/share/sQSrVwHF28) to for user guidance to navigate the chatbot.
