FROM nginx:1.27-alpine
COPY . /usr/share/nginx/html
RUN cp /usr/share/nginx/html/ARCADE_COMMAND_DECK.html /usr/share/nginx/html/index.html
EXPOSE 80
