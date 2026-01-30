FROM nginx:1.25-alpine

# Install certbot and dependencies
RUN apk add --no-cache \
    certbot \
    certbot-nginx \
    openssl \
    bash \
    curl \
    dcron

# Create directories
RUN mkdir -p /var/www/certbot \
    /etc/nginx/certs \
    /etc/nginx/conf.d \
    /var/log/nginx \
    /etc/letsencrypt

# Copy nginx configurations
COPY nginx.conf /etc/nginx/nginx.conf.prod
COPY nginx-dev.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/

# Copy startup script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Generate self-signed certificates for development
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/certs/server.key \
    -out /etc/nginx/certs/server.crt \
    -subj "/C=US/ST=Dev/L=Local/O=Dogcatcher/CN=localhost" && \
    # Create placeholder CA cert for development
    cp /etc/nginx/certs/server.crt /etc/nginx/certs/ca.crt

# Expose ports
EXPOSE 80 443 8443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
