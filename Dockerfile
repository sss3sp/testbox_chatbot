# Use the official Rasa image as the base image
FROM rasa/rasa:3.5.0-full

# Set the working directory
WORKDIR /app

# Copy the project files into the Docker image

COPY data actions models config.yml credentials.yml domain.yml endpoints.yml graph.html story_graph.dot /app/

USER root

COPY ./data /app/data

RUN rasa train

VOLUME /app
VOLUME /app/data
VOLUME /app/models

CMD ["run","-m","/app/models","--enable-api","--cors","*","--debug" ,"--endpoints", "endpoints.yml", "--log-file", "out.log", "--debug"]


