# gunicorn_config.py
command = '/usr/bin/gunicorn'
pythonpath = '/app'
bind = '0.0.0.0:8000'
workers = 3