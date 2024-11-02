FROM node:18-slim

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend code
COPY . .

# Expose port 5173 (Vite's default)
EXPOSE 5173

# Start the development server
# The --host flag allows connections from outside the container
CMD ["npm", "run", "dev", "--", "--host"]