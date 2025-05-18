Get your API key from the [OS Data Hub](https://osdatahub.os.uk/)

Add these to your API key
- OS NGD API – Features
- OS Linked Identifiers API
- OS Places API
  
setup your API key
- copy .env.local to .env
- edit .env to include Key
- check that the key file is not listed as a change to be committed

Run the server with
```bash
python3 src/server.py --transport sse
```

The server will give an error here:
{"detail":"Authentication required"}

and the server will show the interaction
Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:46984 - "GET / HTTP/1.1" 401 Unauthorized
INFO:     127.0.0.1:46984 - "GET /favicon.ico HTTP/1.1" 401 Unauthorized

This is because there is no access without authentication



