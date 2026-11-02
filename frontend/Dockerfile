# frontend/Dockerfile
FROM nginx:alpine

# Copy frontend static files
COPY frontend/ /usr/share/nginx/html

EXPOSE 80 # Nginx default HTTP port

CMD ["nginx", "-g", "daemon off;"]
