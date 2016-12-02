# Biomaj user

Biomaj user management library

Creation/deletion/... scripts should not be accessible to end user, only to admin.
End users can have access to their API Key via the biomaj-watcher interface.


# Web server

    export BIOMAJ_CONFIG=path_to_config.yml
    gunicorn biomaj_user.biomaj_user_service:app

Web processes should be behind a proxy/load balancer, API base url /api/user

# Managing users

    usage: biomaj-users.py [-h] -A ACTION [-C </path/to/config.yml>] [-E EMAIL] -U <username> [-P <password>]

Availables actions: create, delete, update, view, renew (apikey) 
