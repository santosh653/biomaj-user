# Biomaj user

Biomaj user management library

# Status

development

# Web server

In bin directory:
export BIOMAJ_CONFIG=path_to_config.yml
gunicorn biomaj_user_service:app

Web processes should be behind a proxy/load balancer, API base url /api/user

