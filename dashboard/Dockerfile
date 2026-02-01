FROM nginx:alpine

# Copy dashboard files to nginx html directory
COPY index.html /usr/share/nginx/html/
COPY larry-status.json /usr/share/nginx/html/
COPY DASHBOARD.md /usr/share/nginx/html/
COPY PROJECTS.md /usr/share/nginx/html/
COPY tasks.json /usr/share/nginx/html/
COPY basic-dashboard.yaml /usr/share/nginx/html/
COPY home-assistant-dashboard.yaml /usr/share/nginx/html/

# Expose port 8888
EXPOSE 8888

# Configure nginx to listen on port 8888
RUN echo "server { listen 8888; listen [::]:8888; root /usr/share/nginx/html; index index.html; location / { try_files \$uri \$uri/ /index.html; } }" > /etc/nginx/conf.d/default.conf

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
