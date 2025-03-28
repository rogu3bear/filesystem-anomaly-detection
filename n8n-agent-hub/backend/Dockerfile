FROM node:18-alpine

WORKDIR /usr/src/app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

# Build TypeScript files
RUN npm run build

# Expose API port
EXPOSE 3000

# Start the server
CMD ["npm", "start"] 