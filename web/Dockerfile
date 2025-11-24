FROM nginx:stable-alpine

# Copy static site into nginx html dir
WORKDIR /usr/share/nginx/html
COPY static ./

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
