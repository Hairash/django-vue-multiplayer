# django-vue-multiplayer
Test multiplayer application using Django/Vue and websockets

# How to install
### Server
1. Install requirements  
`pip install -r requirements.txt`

### Client
1. Install packages  
`npm i`

# How to run
### Server
1. Run redis  
`redis-server`
2. Run daphne  
`daphne django_vue_multiplayer.asgi:application`

### Client
1. Run vue:  
`npm run serve`
