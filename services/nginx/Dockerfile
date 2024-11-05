# Build the frontend
FROM node:18-alpine as frontend-builder

# Add build argument
ARG API_BASE_URL
ENV VITE_API_URL=${API_BASE_URL}

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ .

# Build the app
RUN npm run build && \
    echo "Frontend build complete. Contents of dist/:" && \
    ls -la dist/

# Final nginx image
FROM nginx:alpine

# Copy nginx configuration
COPY nginx/conf/default.conf /etc/nginx/conf.d/

# Copy built frontend files to nginx html directory
COPY --from=frontend-builder /app/dist/ /usr/share/nginx/html/spotify-connector/

# Verify files were copied
RUN echo "Contents of /usr/share/nginx/html/spotify-connector/:" && \
    ls -la /usr/share/nginx/html/spotify-connector/

# The container will use our custom nginx config
CMD ["nginx", "-g", "daemon off;"]