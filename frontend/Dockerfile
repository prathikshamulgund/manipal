FROM nginx:alpine

RUN rm -rf /usr/share/nginx/html/*

# Copy Angular app first
COPY dist/mining-copilot /usr/share/nginx/html

# Copy login page to a separate route
COPY index.html /usr/share/nginx/html/login.html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]