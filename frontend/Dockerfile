FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
COPY data.html /usr/share/nginx/html/data.html
COPY explorer.html /usr/share/nginx/html/explorer.html
COPY browse.html /usr/share/nginx/html/browse.html

EXPOSE 80
